import ast
import logging
import os
import re
from collections import defaultdict
from functools import lru_cache
from tqdm import tqdm

import openai
import torch
import networkx as nx
from transformers import AutoModel, AutoTokenizer
from dotenv import load_dotenv
from pathlib import Path
from typing import Literal
from rapidfuzz import process, fuzz

from smart_thinking_llm.datasets.data_classes import (
    Entity,
    EntityID,
    Relation,
    RelationID,
)
from smart_thinking_llm.utils import (
    cosine_similarity_normalized_embeddings,
    get_embedding_batch,
    init_basic_logger,
    make_openai_request,
)

load_dotenv()


class Graph:
    def __init__(
        self, entity_to_entity_struct: defaultdict[Entity, dict[Relation, Entity]]
    ):
        self.entity_to_entity_struct = entity_to_entity_struct
        self.graph = nx.DiGraph()
        for entity_1, relations in entity_to_entity_struct.items():
            self.graph.add_node(entity_1, label=entity_1.id._id)
            for relation, entity_2 in relations.items():
                if entity_2 not in self.graph:
                    self.graph.add_node(entity_2, label=entity_2.id._id)
                self.graph.add_edge(entity_1, entity_2, label=relation.id._id)

    @staticmethod
    def node_match(n1, n2):
        return n1["label"] == n2["label"]

    @staticmethod
    def edge_match(e1, e2):
        return e1["label"] == e2["label"]

    def compare_to(
        self,
        other: "Graph",
        node_del_cost: float = 1.0,
        node_ins_cost: float = 1.0,
        edge_del_cost: float = 1.0,
        edge_ins_cost: float = 1.0,
    ) -> float:
        # TODO: add edge_subst_cost and node_subst_cost
        node_del = lambda _: node_del_cost
        node_ins = lambda _: node_ins_cost
        edge_del = lambda _: edge_del_cost
        edge_ins = lambda _: edge_ins_cost
        return nx.graph_edit_distance(
            self.graph,
            other.graph,
            node_match=self.node_match,
            edge_match=self.edge_match,
            node_del_cost=node_del,
            node_ins_cost=node_ins,
            edge_del_cost=edge_del,
            edge_ins_cost=edge_ins,
        )

    def __str__(self) -> str:
        if not self.entity_to_entity_struct:
            return "Graph is empty."

        def get_repr(item: object) -> str:
            """Helper для читаемого представления Entity/Relation"""
            aliases = getattr(item, "aliases", [])
            item_id = getattr(item, "id", "")
            name = aliases[0] if aliases else "N/A"
            return f"{name} ({item_id})"

        output_lines = []

        # Находим корневые узлы (те, что не являются объектами ни одной связи)
        all_subjects = set(self.entity_to_entity_struct.keys())
        all_objects = {
            obj
            for relations_dict in self.entity_to_entity_struct.values()
            for obj in relations_dict.values()
        }
        root_nodes = sorted(
            [s for s in all_subjects if s not in all_objects],
            key=lambda x: str(x.id),
        )

        # Узлы которые и субъекты и объекты (могут быть часть циклов)
        other_nodes = sorted(
            [s for s in all_subjects if s in all_objects],
            key=lambda x: str(x.id),
        )

        visited_globally = set()

        def build_tree(
            node: Entity, prefix: str, is_root: bool, visited_in_path: set[Entity]
        ):
            """Рекурсивное построение дерева с отслеживанием пути для циклов"""

            if is_root:
                output_lines.append(f"[{get_repr(node)}]")

            # Проверяем цикл: если узел уже в текущем пути обхода
            if node in visited_in_path:
                return

            visited_globally.add(node)
            visited_in_path.add(node)

            # Получаем дочерние связи
            if node not in self.entity_to_entity_struct:
                return

            relations = self.entity_to_entity_struct[node]
            children = sorted(list(relations.items()), key=lambda x: str(x[0].id))

            for i, (relation, obj) in enumerate(children):
                is_last = i == len(children) - 1
                connector = "└──" if is_last else "├──"

                # Проверяем, создаст ли этот объект цикл
                if obj in visited_in_path:
                    output_lines.append(
                        f"{prefix}{connector} {get_repr(relation)}: [{get_repr(obj)}] ⟲ (cycle)"
                    )
                else:
                    output_lines.append(
                        f"{prefix}{connector} {get_repr(relation)}: [{get_repr(obj)}]"
                    )

                    # Рекурсивно обрабатываем только Entity
                    if isinstance(obj, Entity):
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        build_tree(obj, new_prefix, False, visited_in_path.copy())

            visited_in_path.remove(node)

        # Обрабатываем все компоненты графа
        for node in root_nodes + other_nodes:
            if node not in visited_globally:
                build_tree(node, "", True, set())
                output_lines.append("")

        return "\n".join(output_lines).rstrip()


class GraphCreator:
    def __init__(
        self,
        entity_aliases_filepath: Path,
        relation_aliases_filepath: Path,
        dataset_filepath: Path,
        triplets_prompt_filepath: Path,
        openai_client: openai.OpenAI,
        triplets_model: Literal[
            "gpt-4.1-2025-04-14",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4.1-nano-2025-04-14",
        ] = "gpt-4.1-nano-2025-04-14",
        norm_lev_threshold: float = 0.3,
        parse_graph_strategy: Literal[
            "no_info",  # без знаний о сущностях внутри одной тройки или каких-либо еще
            "entities_info",  # в коде используется информация о предсказанных подряд entity
        ] = "entities_info",
    ):
        self.entity_aliases_filepath = entity_aliases_filepath
        self.relation_aliases_filepath = relation_aliases_filepath
        self.dataset_filepath = dataset_filepath
        self.triplets_prompt_filepath = triplets_prompt_filepath
        self.triplets_model = triplets_model
        self.openai_client = openai_client
        self.logger = init_basic_logger("GraphCreator", logging.INFO)
        self.norm_lev_threshold = norm_lev_threshold
        self.parse_graph_strategy = parse_graph_strategy

        with open(self.triplets_prompt_filepath, mode="r", encoding="utf-8") as f:
            self.triplets_prompt = f.read()

        # Создаем индекс алиасов для быстрого поиска
        self.logger.info("Building alias index for fast entity lookup...")
        self._alias_to_entities = dict()
        self.entity_to_aliases = defaultdict(list)
        self._all_aliases = []  # Список для rapidfuzz

        with open(self.entity_aliases_filepath, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in tqdm(
                lines, desc="Building entity alias index", total=len(lines)
            ):
                splitted_line = line.strip().split("\t")
                entity_id = splitted_line[0]
                aliases = splitted_line[1:]
                for alias in aliases:
                    normalized_alias = alias.lower().strip()
                    self._alias_to_entities[normalized_alias] = entity_id
                    self._all_aliases.append(normalized_alias)
                self.entity_to_aliases[entity_id] = aliases

        self._alias_to_relation = {}
        self._relation_to_aliases = defaultdict(list)
        with open(self.relation_aliases_filepath, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in tqdm(
                lines, desc="Building relation alias index", total=len(lines)
            ):
                splitted_line = line.strip().split("\t")
                relation_id = splitted_line[0]
                aliases = splitted_line[1:]
                for alias in aliases:
                    normalized_alias = alias.lower().strip()
                    self._alias_to_relation[normalized_alias] = relation_id
                self._relation_to_aliases[relation_id] = aliases

        self._dataset_index = defaultdict(lambda: defaultdict(list))
        # matrix of entities to entities with relations lists [subject][answer] = list[relations]
        with open(self.dataset_filepath, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in tqdm(lines, desc="Building dataset index", total=len(lines)):
                splitted_line = line.strip().split("\t")
                subject = splitted_line[0]
                relation = splitted_line[1]
                answer = splitted_line[2]
                self._dataset_index[subject][answer].append(relation)

        self.logger.info(
            f"Alias index built with {len(self._alias_to_entities)} unique aliases"
        )

    def parse_triplets(self, triplets: str) -> defaultdict[str, dict[str, str]]:
        # Check if triplets string matches the expected format using regex
        # Expected format: [("subject1", "relation1", "object1"), ("subject2", "relation2", "object2"), ...]
        triplet_pattern = r'^\s*\[\s*(?:\(\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*\)\s*(?:,\s*\(\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*\)\s*)*)?\s*\]\s*$'
        if not re.match(triplet_pattern, triplets.strip().replace("\n", "")):
            self.logger.warning(
                f"Triplets string does not match expected format: {triplets}"
            )
            return defaultdict(dict)
        triplets = triplets.strip().replace("\n", "")
        triplets_list = ast.literal_eval(triplets)
        triplets_dict = defaultdict(dict)
        for triplet in triplets_list:
            subject, question, answer = triplet
            triplets_dict[subject][question] = answer
        return triplets_dict

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return GraphCreator.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    @lru_cache(maxsize=1000)
    def _find_entity_by_name(self, name: str) -> Entity:
        normalized_name = name.lower().strip()

        result = process.extractOne(
            normalized_name,
            self._all_aliases,
            scorer=fuzz.token_ratio,
            score_cutoff=(1 - self.norm_lev_threshold) * 100,
        )

        if result is None:
            raise ValueError(f"Entity {name} not found")

        matched_alias, _, _ = result

        entity_id = self._alias_to_entities[matched_alias]
        entity = Entity(EntityID(entity_id), self.entity_to_aliases[entity_id])
        return entity

    def _find_relation_by_name_no_info(
        self, relation_name: str, entity_root: Entity
    ) -> Relation:
        # Собираем все возможные связи для этой пары сущностей
        normalized_relation_name = relation_name.lower().strip()

        # Сначала точное совпадение
        if normalized_relation_name in self._alias_to_relation:
            relation_id = self._alias_to_relation[normalized_relation_name]
            relation = Relation(
                RelationID(relation_id), self._relation_to_aliases[relation_id]
            )
            return relation

        relation_ids = []
        for relations in self._dataset_index[entity_root.id._id].values():
            relation_ids.extend(relations)

        relations_aliases = []
        for relation_id in relation_ids:
            relations_aliases.extend(self._relation_to_aliases[relation_id])

        # Fuzzy matching с rapidfuzz
        result = process.extractOne(
            normalized_relation_name,
            relations_aliases,
            scorer=fuzz.token_ratio,
        )
        if result is None:
            raise ValueError(f"Relation {relation_name} not found")

        matched_alias, _, _ = result

        relation_id = self._alias_to_relation[matched_alias]
        relation = Relation(
            RelationID(relation_id), self._relation_to_aliases[relation_id]
        )
        return relation

    def _parse_graph_structure_no_info(
        self, triplets_dict: defaultdict[str, dict[str, str]]
    ) -> defaultdict[Entity, dict[Relation, Entity]]:
        graph_structure = defaultdict(dict)
        for subject, relations in triplets_dict.items():
            try:
                subject_entity = self._find_entity_by_name(subject.lower().strip())
            except ValueError as e:
                self.logger.warning(
                    f"Skip triplet ({subject}, {relations}) because subject is not found in wikidataset"
                )
                continue
            for relation, answer in relations.items():
                try:
                    relation = self._find_relation_by_name_no_info(
                        relation.lower().strip(), subject_entity.lower().strip()
                    )
                except ValueError as e:
                    self.logger.warning(
                        f"Relation {relation} not found. {e}. Skip triplet ({subject}, {relations})"
                    )
                    continue
                try:
                    answer_entity = self._find_entity_by_name(answer.lower().strip())
                except ValueError as e:
                    self.logger.warning(
                        f"Skip triplet ({subject}, {relations}, {answer}) because answer is not found in wikidataset"
                    )
                    continue
                graph_structure[subject_entity][relation] = answer_entity
        return graph_structure

    @lru_cache(maxsize=1000)
    def _find_relation_by_name_entities_info(
        self, relation_name: str, entity_start: Entity, entity_end: Entity
    ) -> Relation:
        # Собираем все возможные связи для этой пары сущностей
        normalized_relation_name = relation_name.lower().strip()

        # Сначала точное совпадение
        if normalized_relation_name in self._alias_to_relation:
            relation_id = self._alias_to_relation[normalized_relation_name]
            relation = Relation(
                RelationID(relation_id), self._relation_to_aliases[relation_id]
            )
            return relation

        relation_ids = self._dataset_index[entity_start.id._id][entity_end.id._id]

        relations_aliases = []
        for relation_id in relation_ids:
            relations_aliases.extend(self._relation_to_aliases[relation_id])

        # Fuzzy matching с rapidfuzz
        result = process.extractOne(
            normalized_relation_name,
            relations_aliases,
            scorer=fuzz.token_ratio,
        )
        if result is None:
            raise ValueError(f"Relation {relation_name} not found")

        matched_alias, _, _ = result

        relation_id = self._alias_to_relation[matched_alias]
        relation = Relation(
            RelationID(relation_id), self._relation_to_aliases[relation_id]
        )
        return relation

    def _parse_graph_structure_entities_info(
        self, triplets_dict: defaultdict[str, dict[str, str]]
    ) -> defaultdict[Entity, dict[Relation, Entity]]:
        graph_structure = defaultdict(dict)
        for subject, relations in triplets_dict.items():
            try:
                subject_entity = self._find_entity_by_name(subject.lower().strip())
            except ValueError as _:
                self.logger.warning(
                    f"Skip triplet ({subject}, {relations}) because subject is not found in wikidataset"
                )
                continue
            for relation, answer in relations.items():
                try:
                    answer_entity = self._find_entity_by_name(answer.lower().strip())
                except ValueError as _:
                    self.logger.warning(
                        f"Skip triplet ({subject}, {relation}, {answer}) because answer is not found in wikidataset"
                    )
                    continue
                try:
                    relation_entity = self._find_relation_by_name_entities_info(
                        relation.strip().lower(), subject_entity, answer_entity
                    )
                except ValueError as _:
                    self.logger.warning(
                        f"Skip triplet ({subject}, {relation}, {answer}) because relation is not found"
                    )
                    continue
                graph_structure[subject_entity][relation_entity] = answer_entity
        return graph_structure

    def parse_graph_structure(
        self, triplets_dict: defaultdict[str, dict[str, str]]
    ) -> defaultdict[Entity, dict[Relation, Entity]]:
        if self.parse_graph_strategy == "no_info":
            return self._parse_graph_structure_no_info(triplets_dict)
        elif self.parse_graph_strategy == "entities_info":
            return self._parse_graph_structure_entities_info(triplets_dict)
        else:
            raise ValueError(
                f"Invalid parse graph strategy: {self.parse_graph_strategy}"
            )

    def get_graph_from_path(self, path: str) -> Graph:
        graph_structure = defaultdict(dict)
        triple_pattern = re.compile(r"(?=(Q\d+)-(P\d+)-(Q\d+))")

        for match in triple_pattern.finditer(path):
            subject_id, predicate_id, obj_id = match.groups()
            subject = Entity(EntityID(subject_id), self.entity_to_aliases[subject_id])
            predicate = Relation(
                RelationID(predicate_id), self._relation_to_aliases[predicate_id]
            )
            obj = Entity(EntityID(obj_id), self.entity_to_aliases[obj_id])
            graph_structure[subject][predicate] = obj

        return Graph(graph_structure)

    def __call__(self, model_answer: str) -> Graph:
        prompt = self.triplets_prompt % model_answer
        # [("Donatus Djagom", "religious affiliation", "Catholicism"), ("Catholicism", "headquarters located", "Vatican City")]
        triplets = make_openai_request(
            self.openai_client, self.triplets_model, prompt, self.logger
        )
        triplets_dict = self.parse_triplets(
            triplets
        )  # {"Donatus Djagom": {"religious affiliation": "Catholicism"}, "Catholicism": {"headquarters located": "Vatican City"}}
        graph_structure = self.parse_graph_structure(triplets_dict)
        return Graph(graph_structure)


class GraphCreatorWithEmbeddings(GraphCreator):
    def __init__(
        self,
        entity_aliases_filepath: Path,
        relation_aliases_filepath: Path,
        dataset_filepath: Path,
        triplets_prompt_filepath: Path,
        openai_client: openai.OpenAI,
        triplets_model: Literal[
            "gpt-4.1-2025-04-14",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4.1-nano-2025-04-14",
        ] = "gpt-4.1-nano-2025-04-14",
        norm_lev_threshold: float = 0.3,
        parse_graph_strategy: Literal[
            "no_info",  # без знаний о сущностях внутри одной тройки или каких-либо еще
            "entities_info",  # в коде используется информация о предсказанных подряд entity
        ] = "entities_info",
        embeddings_model: Literal[
            "Qwen/Qwen3-Embedding-4B"
        ] = "Qwen/Qwen3-Embedding-4B",
        device: torch.device = torch.device("cuda:1"),
    ):
        super().__init__(
            entity_aliases_filepath,
            relation_aliases_filepath,
            dataset_filepath,
            triplets_prompt_filepath,
            openai_client,
            triplets_model,
            norm_lev_threshold,
            parse_graph_strategy,
        )
        self.embeddings_tokenizer = AutoTokenizer.from_pretrained(
            embeddings_model,
            padding_side="left",
            use_fast=True,
        )
        self.embeddings_model = AutoModel.from_pretrained(
            embeddings_model,
            torch_dtype=torch.float16,
            load_in_8bit=True,
            low_cpu_mem_usage=True,
            device_map={"": device.index},
        )
        self.embeddings_model.eval()

    @lru_cache(maxsize=1000)
    def _find_relation_by_name_entities_info(
        self, relation_name: str, entity_start: Entity, entity_end: Entity
    ) -> Relation:
        """
        Find relation by name using embeddings
        """
        # Собираем все возможные связи для этой пары сущностей
        normalized_relation_name = relation_name.lower().strip()

        # Сначала точное совпадение
        if normalized_relation_name in self._alias_to_relation:
            relation_id = self._alias_to_relation[normalized_relation_name]
            relation = Relation(
                RelationID(relation_id), self._relation_to_aliases[relation_id]
            )
            return relation

        relation_ids = self._dataset_index[entity_start.id._id][entity_end.id._id]

        relations_aliases = []
        for relation_id in relation_ids:
            relations_aliases.extend(self._relation_to_aliases[relation_id])

        # Fuzzy matching с rapidfuzz
        result = process.extract(
            normalized_relation_name,
            relations_aliases,
            scorer=fuzz.token_ratio,
            limit=10
        )
        if result is None:
            raise ValueError(f"Relation {relation_name} not found")

        matched_aliases = [alias for alias, _, _ in result]
        embeddings = get_embedding_batch(
            matched_aliases,
            self.embeddings_tokenizer,
            self.embeddings_model,
            normalize=True,
            max_length=64
        ) # [len(matched_aliases), embedding_dim]
        distances = cosine_similarity_normalized_embeddings(self.query_embedding, embeddings) # [len(matched_aliases), ]
        index_of_closest_embedding = distances.index(max(distances)) # int
        closest_alias = matched_aliases[index_of_closest_embedding]

        relation_id = self._alias_to_relation[closest_alias]
        relation = Relation(
            RelationID(relation_id), self._relation_to_aliases[relation_id]
        )
        return relation

    @lru_cache(maxsize=1000)
    def _find_entity_by_name(self, name: str) -> Entity:
        """
        Find entity by name using embeddings
        """
        normalized_name = name.lower().strip()

        result = process.extract(
            normalized_name,
            self._all_aliases,
            scorer=fuzz.token_ratio,
            score_cutoff=(1 - self.norm_lev_threshold) * 100,
            limit=10,
        )

        if result is None:
            raise ValueError(f"Entity {name} not found")

        matched_aliases = [alias for alias, _, _ in result]

        embeddings = get_embedding_batch(
            matched_aliases,
            self.embeddings_tokenizer,
            self.embeddings_model,
            normalize=True,
            max_length=64
        ) # [len(matched_aliases), embedding_dim]
        distances = cosine_similarity_normalized_embeddings(self.query_embedding, embeddings) # [len(matched_aliases), ]
        index_of_closest_embedding = distances.index(max(distances)) # int
        closest_alias = matched_aliases[index_of_closest_embedding]

        entity_id = self._alias_to_entities[closest_alias]
        entity = Entity(EntityID(entity_id), self.entity_to_aliases[entity_id])
        return entity

    def __call__(self, model_answer: str) -> Graph:
        prompt = self.triplets_prompt % model_answer
        # [("Donatus Djagom", "religious affiliation", "Catholicism"), ("Catholicism", "headquarters located", "Vatican City")]
        triplets = make_openai_request(
            self.openai_client, self.triplets_model, prompt, self.logger
        )
        triplets_dict = self.parse_triplets(
            triplets
        )  # {"Donatus Djagom": {"religious affiliation": "Catholicism"}, "Catholicism": {"headquarters located": "Vatican City"}}
        self.query_embedding = get_embedding_batch(
            [model_answer],
            self.embeddings_tokenizer,
            self.embeddings_model,
            normalize=True,
            max_length=64
        )[0] # [embedding_dim, ]
        graph_structure = self.parse_graph_structure(triplets_dict)
        return Graph(graph_structure)


### !! USE EXAMPLES TO TEST THE GRAPH CREATION !!
def main():
    openai.api_key = os.environ.get("OPENAI_APIKEY")
    openai_client = openai.OpenAI()

    graph_creator = GraphCreator(
        entity_aliases_filepath=Path(
            "data/raw_data/wikidata5m_alias/wikidata5m_entity.txt"
        ),
        relation_aliases_filepath=Path(
            "data/raw_data/wikidata5m_alias/wikidata5m_relation.txt"
        ),
        dataset_filepath=Path(
            "data/raw_data/wikidata5m_transductive/wikidata5m_transductive_train.txt"
        ),
        triplets_prompt_filepath=Path(
            "smart_thinking_llm/prompts/generate_triplets_prompt.txt"
        ),
        openai_client=openai_client,
        parse_graph_strategy="entities_info",
    )

    # 2hop graph
    model_answer = """Feyenoord Rotterdam is based in the Netherlands.  
The head of government of the Netherlands is the Prime Minister.  
The Prime Minister of the Netherlands is Mark Rutte."""

    graph = graph_creator(model_answer)

    ground_truth_graph = Graph(
        {
            Entity(EntityID("Q134241"), aliases=["Feyenoord Rotterdam"]): {
                Relation(RelationID("P17"), aliases=["based in"]): Entity(
                    EntityID("Q55"), aliases=["the Netherlands"]
                ),
            },
            Entity(EntityID("Q55"), aliases=["the Netherlands"]): {
                Relation(RelationID("P6"), aliases=["head of government"]): Entity(
                    EntityID("Q57792"),
                    aliases=["Marc Rutte", "mark rutt", "rutte, mark", "Mark Rutte"],
                ),
            },
        }
    )
    print("=" * 50, "2hop graph", "=" * 50)
    print("*" * 10, "Generated graph", "*" * 10)
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 10))
    nx.draw(graph.graph, with_labels=True)
    plt.savefig("generated_graph_2hop.png")
    plt.close()
    print("*" * 10, "Ground truth graph", "*" * 10)
    print(ground_truth_graph)
    print(f"Graph edit distance: {graph.compare_to(ground_truth_graph)}")
    print("=" * 100)

    # 3hop graph
    model_answer = """Miyankuh-e Gharbi is located in Iran. Iran shares a border with Pakistan. The highest peak in Pakistan is K2, which rises to 8,611 metres above sea level."""

    graph = graph_creator(model_answer)

    ground_truth_graph = Graph(
        {
            Entity(EntityID("Q6884371"), aliases=["Miyankuh-e Gharbi"]): {
                Relation(RelationID("P17"), aliases=["country"]): Entity(
                    EntityID("Q794"), aliases=["Persian State of Iran"]
                ),
            },
            Entity(EntityID("Q794"), aliases=["Persian State of Iran"]): {
                Relation(RelationID("P47"), aliases=["shares border with"]): Entity(
                    EntityID("Q227"), aliases=["azerbajani"]
                ),
            },
            Entity(EntityID("Q227"), aliases=["Pakistan"]): {
                Relation(RelationID("P610"), aliases=["highest peak"]): Entity(
                    EntityID("Q725591"), aliases=["bazardüzü"]
                ),
            },
        }
    )
    print("=" * 50, "3hop graph", "=" * 50)
    print("*" * 10, "Generated graph", "*" * 10)
    plt.figure(figsize=(10, 10))
    nx.draw(graph.graph, with_labels=True)
    plt.savefig("generated_graph_3hop.png")
    plt.close()
    print("*" * 10, "Ground truth graph", "*" * 10)
    print(ground_truth_graph)
    print(f"Graph edit distance: {graph.compare_to(ground_truth_graph)}")
    print("=" * 100)


if __name__ == "__main__":
    main()

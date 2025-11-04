"""
Forward Entailer - Stage 2 of Stanford OpenIE

Uses natural logic to find entailed shortenings of a sentence by deleting
dependency edges while maintaining valid entailment.

Ported from ForwardEntailerSearchProblem.java (384 lines)
"""

from collections import deque
from dataclasses import dataclass
from typing import Optional

from spacy.tokens import Doc, Token

from .dependency_relations import for_dependency_deletion
from .natural_logic_weights import NaturalLogicWeights
from .polarity import Polarity
from .sentence_fragment import SentenceFragment
from .text_utils import reconstruct_text


@dataclass
class SearchResult:
    """
    A result from the forward entailment search.

    Attributes:
        doc: The shortened dependency tree
        deleted_edges: List of deleted edge labels
        confidence: Deletion probability score (0-1)
    """

    doc: Doc
    deleted_edges: list[str]
    confidence: float

    def to_fragment(self, truth_of_premise: bool) -> SentenceFragment:
        """Convert to a SentenceFragment."""
        fragment = SentenceFragment(
            doc=self.doc,
            token_indices=None,  # Use all tokens in doc
            assumed_truth=truth_of_premise,
            score=self.confidence,
        )
        return fragment


@dataclass
class SearchState:
    """
    A search state representing a partial shortening.

    Attributes:
        deletion_mask: BitSet indicating which tokens are deleted
        current_index: Current token index in topological order
        doc: Current dependency tree (with deletions applied)
        last_deleted_edge: Last edge label we deleted
        source: Previous search state (for backtracking)
        score: Cumulative deletion probability score
    """

    deletion_mask: set[int]
    current_index: int
    doc: Doc
    last_deleted_edge: str | None
    source: Optional["SearchState"]
    score: float


class ForwardEntailer:
    """
    Stage 2 of Stanford OpenIE: Shorten clauses via natural logic entailment.

    Uses DFS search to explore deletions of dependency edges, validating
    each deletion maintains valid entailment using natural logic relations.

    Ports ForwardEntailerSearchProblem.java
    """

    def __init__(
        self,
        weights: NaturalLogicWeights | None = None,
        max_ticks: int = 5000,
        max_results: int = 100,
        nlp=None,
    ):
        """
        Initialize the forward entailer.

        Args:
            weights: Natural logic weights (loads default if None)
            max_ticks: Maximum search iterations
            max_results: Maximum number of results to return
            nlp: spaCy Language instance (loads en_core_web_sm if None)
        """
        self.weights = weights if weights else NaturalLogicWeights()
        self.max_ticks = max_ticks
        self.max_results = max_results

        # Load spaCy parser for creating new docs after deletions
        if nlp is None:
            import spacy

            self.nlp = spacy.load("en_core_web_sm")
        else:
            self.nlp = nlp

    def entail(self, doc: Doc, truth_of_premise: bool = True) -> list[SentenceFragment]:
        """
        Find entailed shortenings of the input sentence.

        Args:
            doc: Spacy Doc containing the sentence
            truth_of_premise: Whether the premise is true (vs false)

        Returns:
            List of entailed sentence fragments, sorted by confidence
        """
        results = self._search(doc, truth_of_premise)

        # Convert to sentence fragments
        fragments = [r.to_fragment(truth_of_premise) for r in results if len(r.doc) > 0]

        # Sort by score descending
        fragments.sort(key=lambda f: f.score, reverse=True)

        return fragments

    def _search(self, doc: Doc, truth_of_premise: bool) -> list[SearchResult]:
        """
        The search algorithm for finding entailed shortenings.

        Ports ForwardEntailerSearchProblem.searchImplementation()
        (lines 132-359)

        Args:
            doc: Input dependency tree
            truth_of_premise: Whether premise is true

        Returns:
            List of search results
        """
        # Make a copy to avoid modifying the input
        parse_tree = doc

        # Pre-process: remove common determiners
        # (lines 136-150)
        determiner_removals = []
        tokens_to_remove = []

        for token in parse_tree:
            word_lower = token.text.lower()
            if word_lower in ("the", "a", "an", "this", "that", "those", "these"):
                if token.dep_ == "det" or self._is_leaf(token, parse_tree):
                    tokens_to_remove.append(token)
                    determiner_removals.append("det")

        # Create modified doc without determiners
        if tokens_to_remove:
            parse_tree = self._remove_tokens(parse_tree, {t.i for t in tokens_to_remove})

        # Pre-process: cut conj:and edges that create multiple parents
        # (lines 152-167)
        # TODO: For now, skip this step - it's complex and rarely affects results

        # Find subject/object split
        # (lines 173-202)
        is_subject = self._find_subject_nodes(parse_tree)

        # Initialize results
        results: list[SearchResult] = []

        # Add determiner-only result if we removed any
        if determiner_removals:
            # Find the determiner token (if it exists)
            det_token = next((t for t in doc if t.dep_ == "det"), None)

            # Only add result if we found a determiner token
            # (avoid passing None to deletion_probability which would crash)
            if det_token is not None:
                det_score = self.weights.deletion_probability(det_token, doc) ** len(
                    determiner_removals
                )
                results.append(
                    SearchResult(
                        doc=parse_tree, deleted_edges=determiner_removals, confidence=det_score
                    )
                )

        # Get topological sort for DFS
        # (lines 226-234)
        topological_order = self._topological_sort(parse_tree)

        if not topological_order:
            return results

        # Initialize DFS fringe (stack)
        # (lines 236-237)
        fringe: deque[SearchState] = deque()
        initial_state = SearchState(
            deletion_mask=set(),
            current_index=0,
            doc=parse_tree,
            last_deleted_edge=None,
            source=None,
            score=1.0,
        )
        fringe.append(initial_state)

        # Run DFS
        # (lines 240-355)
        num_ticks = 0

        while fringe:
            # Check limits
            if num_ticks >= self.max_ticks:
                break
            if len(results) >= self.max_results:
                break

            num_ticks += 1
            state = fringe.pop()

            # Skip if score too low
            if state.score <= 0.0:
                continue

            # Get current word
            if state.current_index >= len(topological_order):
                continue

            current_word = topological_order[state.current_index]

            # Skip if already deleted
            if current_word.i in state.deletion_mask:
                # Move to next index
                next_idx = self._next_undeleted_index(
                    state.current_index + 1, topological_order, state.deletion_mask
                )
                if next_idx is not None:
                    fringe.append(
                        SearchState(
                            deletion_mask=state.deletion_mask,
                            current_index=next_idx,
                            doc=state.doc,
                            last_deleted_edge=None,
                            source=state,
                            score=state.score,
                        )
                    )
                continue

            # Push the case where we DON'T delete
            # (lines 254-271)
            next_idx = self._next_undeleted_index(
                state.current_index + 1, topological_order, state.deletion_mask
            )
            if next_idx is not None:
                fringe.append(
                    SearchState(
                        deletion_mask=state.deletion_mask,
                        current_index=next_idx,
                        doc=state.doc,
                        last_deleted_edge=None,
                        source=state,
                        score=state.score,
                    )
                )

            # Check if we CAN delete this subtree
            # (lines 273-301)
            can_delete = not self._is_root(current_word, state.doc)

            # Get incoming edges to this token
            parent = current_word.head
            if can_delete and parent != current_word:
                edge_relation = current_word.dep_

                # Don't delete from CD parents (numbers)
                if parent.tag_ == "CD":
                    can_delete = False

                # Check natural logic validity
                if can_delete:
                    # Get polarity from token annotation (computed by polarity annotator)
                    token_polarity = (
                        current_word._.polarity
                        if hasattr(current_word._, "polarity") and current_word._.polarity
                        else Polarity.DEFAULT
                    )

                    # Get deletion relation
                    is_subj_node = current_word.i in is_subject
                    lexical_relation = for_dependency_deletion(edge_relation, is_subj_node)

                    # Project through polarity
                    projected_relation = token_polarity.project_lexical_relation(lexical_relation)

                    # Check if this preserves truth
                    truth_result = projected_relation.apply_to_truth_value(truth_of_premise)

                    if not truth_result.is_true():
                        can_delete = False

            # If we can delete, do it
            # (lines 303-354)
            if can_delete:
                # Get descendants
                descendants = self._get_descendants(current_word, state.doc)

                # Check if current_word is part of a hyphenated compound
                # If so, include all compound tokens in deletion to avoid orphaned hyphens
                compound_tokens = self._get_compound_tokens(current_word, state.doc)
                if len(compound_tokens) > 1:
                    # Delete entire compound atomically
                    for comp_token in compound_tokens:
                        descendants.add(comp_token)
                        # Also get descendants of each compound part
                        comp_descendants = self._get_descendants(comp_token, state.doc)
                        descendants.update(comp_descendants)

                # Create new deletion mask
                new_mask = state.deletion_mask.copy()
                for desc in descendants:
                    new_mask.add(desc.i)

                # Apply deletions to create new doc
                new_doc = self._remove_tokens(state.doc, descendants)

                # Compute score
                new_score = state.score
                if parent != current_word:
                    # Get siblings for deletion probability
                    list(parent.children) if parent else []
                    multiplier = self.weights.deletion_probability(current_word, state.doc)
                    new_score *= multiplier

                # Only proceed if score > 0
                if new_score > 0.0:
                    # Register result
                    deleted_edges_list = self._aggregate_deleted_edges(
                        state,
                        [current_word.dep_] if parent != current_word else [],
                        determiner_removals,
                    )

                    results.append(
                        SearchResult(
                            doc=new_doc, deleted_edges=deleted_edges_list, confidence=new_score
                        )
                    )

                    # Push state with deletion
                    next_idx = self._next_undeleted_index(
                        state.current_index + 1, topological_order, new_mask
                    )
                    if next_idx is not None:
                        fringe.append(
                            SearchState(
                                deletion_mask=new_mask,
                                current_index=next_idx,
                                doc=new_doc,
                                last_deleted_edge=current_word.dep_,
                                source=state,
                                score=new_score,
                            )
                        )

        return results

    def _is_leaf(self, token: Token, doc: Doc) -> bool:
        """Check if token has no children."""
        return not any(child.head == token for child in doc)

    def _is_root(self, token: Token, doc: Doc) -> bool:
        """Check if token is the root."""
        return token.dep_ == "ROOT" or token.head == token

    def _remove_tokens(self, doc: Doc, tokens_to_remove) -> Doc:
        """
        Create a new Doc without specified tokens.

        Args:
            doc: Original doc
            tokens_to_remove: Set of Token objects or set of token indices to remove

        Returns:
            New Doc without those tokens
        """
        # Handle both Set[Token] and Set[int]
        if not tokens_to_remove:
            return doc

        # Convert to set of indices
        if isinstance(next(iter(tokens_to_remove)), Token):
            remove_indices = {t.i for t in tokens_to_remove}
        else:
            remove_indices = tokens_to_remove

        # Get indices of tokens to keep
        keep_indices = [i for i in range(len(doc)) if i not in remove_indices]

        if not keep_indices:
            # Return empty doc - create from empty list
            return self.nlp("")

        # Extract text from remaining tokens
        # Preserve spacing where possible
        remaining_tokens = [doc[i] for i in keep_indices]
        reconstructed_text = reconstruct_text(remaining_tokens)

        # Re-parse to get proper dependencies
        new_doc = self.nlp(reconstructed_text)

        return new_doc

    def _find_subject_nodes(self, doc: Doc) -> set[int]:
        """
        Find all nodes that are subjects or descendants of subjects.

        Ports lines 175-202.

        Args:
            doc: Dependency tree

        Returns:
            Set of token indices that are subjects
        """
        is_subject = set()

        for token in doc:
            # Check if this or any ancestor is a subject
            current = token
            depth = 0
            while current and depth < 100:
                if current.dep_.endswith("subj"):
                    is_subject.add(token.i)
                    break

                # Move to parent
                if current.head == current:
                    break
                current = current.head
                depth += 1

        return is_subject

    def _topological_sort(self, doc: Doc) -> list[Token]:
        """
        Topological sort of dependency tree.

        Falls back to left-to-right if not a proper tree.

        Args:
            doc: Dependency tree

        Returns:
            List of tokens in topological order
        """
        # Simple left-to-right order
        # TODO: Implement proper topological sort
        return list(doc)

    def _next_undeleted_index(
        self, start_index: int, topological_order: list[Token], deletion_mask: set[int]
    ) -> int | None:
        """
        Find next undeleted token index.

        Args:
            start_index: Starting index
            topological_order: Tokens in topological order
            deletion_mask: Set of deleted token indices

        Returns:
            Next valid index, or None
        """
        for i in range(start_index, len(topological_order)):
            if topological_order[i].i not in deletion_mask:
                return i
        return None

    def _get_compound_tokens(self, token: Token, doc: Doc) -> set[Token]:
        """
        Get all tokens that are part of the same hyphenated compound as the given token.

        For example, in "antibiotic-resistant", if given "antibiotic", returns
        {"antibiotic", "-", "resistant"} so they can be deleted atomically.

        Args:
            token: Token that may be part of a compound
            doc: Dependency tree

        Returns:
            Set of tokens in the compound (includes the token itself)
        """
        compound_tokens = {token}

        # Check UPWARD: if token is part of a hyphenated compound by looking at siblings
        parent = token.head
        if parent != token:
            siblings = list(parent.children)

            # Check if any sibling is a hyphen (indicates compound)
            has_hyphen = any(sib.text in ("-", "—", "–", "‐") for sib in siblings)

            if has_hyphen:
                # Include all tokens that are part of this compound:
                # - All amod (adjectival modifier) siblings
                # - All hyphen punctuation siblings
                # - The parent if it's also an amod (e.g., resistant in antibiotic-resistant strains)
                for sibling in siblings:
                    if sibling.dep_ == "amod" or sibling.text in ("-", "—", "–", "‐"):
                        compound_tokens.add(sibling)

                # If parent is also a modifier (e.g., "resistant" modifying "strains"),
                # include it in the compound
                if parent.dep_ == "amod":
                    compound_tokens.add(parent)

        # Check DOWNWARD: if token itself is the head of a hyphenated compound
        children = list(token.children)
        has_hyphen_child = any(child.text in ("-", "—", "–", "‐") for child in children)

        if has_hyphen_child:
            # Include all children that are part of the compound
            for child in children:
                if child.dep_ == "amod" or child.text in ("-", "—", "–", "‐"):
                    compound_tokens.add(child)

        return compound_tokens

    def _get_descendants(self, token: Token, doc: Doc) -> set[Token]:
        """
        Get all descendants of a token in the dependency tree.

        Args:
            token: Root token
            doc: Dependency tree

        Returns:
            Set of descendant tokens (including token itself)
        """
        descendants = {token}
        queue = [token]

        while queue:
            current = queue.pop(0)
            for child in doc:
                if child.head == current and child != current:
                    if child not in descendants:
                        descendants.add(child)
                        queue.append(child)

        return descendants

    def _aggregate_deleted_edges(
        self, state: SearchState, just_deleted: list[str], other_edges: list[str]
    ) -> list[str]:
        """
        Backtrace to collect all deleted edges.

        Ports lines 368-383.

        Args:
            state: Current search state
            just_deleted: Edges just deleted
            other_edges: Other deletions (e.g., determiners)

        Returns:
            Complete list of deleted edges
        """
        result = []
        result.extend(just_deleted)
        result.extend(other_edges)

        # Backtrace
        current = state
        while current is not None:
            if current.last_deleted_edge:
                result.append(current.last_deleted_edge)
            current = current.source

        return result

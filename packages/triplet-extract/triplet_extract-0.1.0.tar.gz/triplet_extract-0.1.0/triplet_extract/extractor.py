"""
Full Stanford OpenIE Pipeline - Pure Python Implementation

Implements the complete 3-stage Stanford OpenIE pipeline:
- Stage 1: ClauseSplitter - Split sentences into entailed clauses
- Stage 2: ForwardEntailer - Find entailed shortenings via natural logic
- Stage 3: RelationTripleSegmenter - Extract (subject, relation, object) triples

Ported from Stanford OpenIE (Angeli et al., 2015).
No Java dependencies - uses Spacy for parsing and our ported models.

Reference:
Angeli, Gabor, Melvin Jose Johnson Premkumar, and Christopher D. Manning.
"Leveraging linguistic structure for open domain information extraction."
ACL 2015.
"""

import logging
from dataclasses import dataclass
from typing import Any

import spacy

from .corenlp_patterns import CoreNLPStyleExtractor
from .normalizer import normalize_quantities

# Import our OpenIE components
from .openie.clause_splitter import ClauseSplitter
from .openie.forward_entailer import ForwardEntailer
from .openie.polarity_annotator import PolarityAnnotator

# Optional: tqdm for progress bars
try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


@dataclass
class Triplet:
    """A subject-relation-object triplet with confidence score."""

    subject: str
    relation: str
    object: str
    confidence: float = 1.0

    # Metadata about extraction path
    from_clause_split: bool = False
    from_entailment: bool = False
    entailment_score: float = 1.0

    def __str__(self):
        return f"({self.subject}, {self.relation}, {self.object})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "relation": self.relation,
            "object": self.object,
            "confidence": self.confidence,
            "from_clause_split": self.from_clause_split,
            "from_entailment": self.from_entailment,
            "entailment_score": self.entailment_score,
        }


class OpenIEExtractor:
    """
    Complete Stanford OpenIE pipeline in pure Python.

    This extractor implements all 3 stages:
    1. ClauseSplitter: Splits sentences into clauses using beam search
    2. ForwardEntailer: Finds entailed shortenings using natural logic
    3. RelationTripleSegmenter: Extracts triples from fragments

    The pipeline produces significantly more triples than simple pattern matching
    by systematically exploring entailed fragments.
    """

    def __init__(
        self,
        nlp: spacy.language.Language | None = None,
        enable_clause_split: bool = True,
        enable_entailment: bool = True,
        min_confidence: float = 0.3,
        filter_aux_edges: bool = True,
        keep_aux_if_alone: bool = True,
    ):
        """
        Initialize the full OpenIE extractor.

        Args:
            nlp: spaCy Language instance (loads en_core_web_sm if None)
            enable_clause_split: Whether to run Stage 1 (ClauseSplitter)
            enable_entailment: Whether to run Stage 2 (ForwardEntailer)
            min_confidence: Minimum confidence threshold for triples
            filter_aux_edges: Remove redundant auxiliary-only triples (e.g., "S -> do -> V")
            keep_aux_if_alone: Keep aux triple if no better alternative exists
        """
        # Initialize spaCy parser
        if nlp is None:
            self.nlp = spacy.load("en_core_web_sm")
        else:
            self.nlp = nlp

        # Configuration
        self.enable_clause_split = enable_clause_split
        self.enable_entailment = enable_entailment
        self.min_confidence = min_confidence
        self.filter_aux_edges = filter_aux_edges
        self.keep_aux_if_alone = keep_aux_if_alone

        # Initialize pipeline stages
        self.polarity_annotator = PolarityAnnotator(self.nlp)
        self.clause_splitter = ClauseSplitter() if enable_clause_split else None
        self.forward_entailer = ForwardEntailer() if enable_entailment else None
        self.triple_segmenter = CoreNLPStyleExtractor(nlp=self.nlp)

        logging.info("Initialized OpenIEExtractor:")
        logging.info("  - Parser: spaCy")
        logging.info(f"  - Clause splitting: {enable_clause_split}")
        logging.info(f"  - Entailment: {enable_entailment}")
        logging.info(f"  - Min confidence: {min_confidence}")

    def __enter__(self):
        """Context manager entry - no resources to initialize."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - no resources to cleanup."""
        return False

    def extract_triplet_objects(self, text: str) -> list[Triplet]:
        """
        Extract triplet objects with full metadata.

        Returns Triplet objects with confidence scores and metadata about
        clause splitting and entailment.

        Args:
            text: Input sentence

        Returns:
            List of extracted Triplet objects with confidence scores
        """
        # This is the original extract_triplets logic
        return self._extract_triplets_internal(text)

    def extract_triplets(self, text: str) -> list[str]:
        """
        Extract triplets from text using the full 3-stage pipeline.

        This is the main interface for compatibility with test scripts.

        Pipeline:
        1. Parse sentence with Spacy
        2. [Stage 1] Split into clauses (optional)
        3. [Stage 2] Find entailed shortenings (optional)
        4. [Stage 3] Extract triples from all fragments

        Args:
            text: Input sentence

        Returns:
            List of triplet strings in format "subject relation object"
        """
        triplet_objects = self._extract_triplets_internal(text)
        return [f"{t.subject} {t.relation} {t.object}" for t in triplet_objects]

    def _extract_triplets_internal(self, text: str) -> list[Triplet]:
        """Internal implementation that returns Triplet objects."""
        # Parse with Spacy
        doc = self.nlp(text)

        # Split into sentences and process each separately
        # This matches Stanford OpenIE behavior and prevents compound detection
        # from failing across sentence boundaries
        sentences = list(doc.sents)

        # Global deduplication across all sentences
        all_triplets = []
        seen_triplets = set()

        for sent in sentences:
            # Process this sentence through the full pipeline
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            # Parse the sentence as its own doc
            sent_doc = self.nlp(sent_text)

            # Annotate polarity (critical for natural logic inference)
            sent_doc = self.polarity_annotator.annotate(sent_doc)

            # Collect fragments to extract from
            fragments = []

            # Start with original sentence
            fragments.append(
                {
                    "doc": sent_doc,
                    "text": sent_text,
                    "score": 1.0,
                    "from_clause_split": False,
                    "from_entailment": False,
                }
            )

            # Stage 1: Clause Splitting
            if self.enable_clause_split and self.clause_splitter:
                try:
                    clause_fragments = self.clause_splitter.split(sent_doc)

                    for frag in clause_fragments:
                        # Skip if score too low
                        if frag.score < self.min_confidence:
                            continue

                        # Convert fragment to text
                        frag_text = str(frag)

                        # Skip if identical to original
                        if frag_text == sent_text:
                            continue

                        fragments.append(
                            {
                                "doc": frag.doc,
                                "text": frag_text,
                                "score": frag.score,
                                "from_clause_split": True,
                                "from_entailment": False,
                            }
                        )

                    logging.debug(f"ClauseSplitter: {len(clause_fragments)} fragments")

                except Exception as e:
                    logging.warning(f"ClauseSplitter failed: {e}")

            # Stage 2: Forward Entailment
            if self.enable_entailment and self.forward_entailer:
                try:
                    # Apply forward entailer to each fragment
                    new_fragments = []

                    for frag_info in fragments:
                        entailed_fragments = self.forward_entailer.entail(
                            frag_info["doc"], truth_of_premise=True
                        )

                        for ent_frag in entailed_fragments:
                            # Skip if score too low
                            if ent_frag.score < self.min_confidence:
                                continue

                            # Convert fragment to text
                            ent_text = str(ent_frag)

                            # Skip if identical to source
                            if ent_text == frag_info["text"]:
                                continue

                            new_fragments.append(
                                {
                                    "doc": ent_frag.doc,
                                    "text": ent_text,
                                    "score": frag_info["score"] * ent_frag.score,
                                    "from_clause_split": frag_info["from_clause_split"],
                                    "from_entailment": True,
                                }
                            )

                    fragments.extend(new_fragments)
                    logging.debug(f"ForwardEntailer: {len(new_fragments)} entailments")

                except Exception as e:
                    logging.warning(f"ForwardEntailer failed: {e}")

            # Stage 3: Relation Triple Segmentation
            for frag_info in fragments:
                try:
                    # Extract triples from this fragment's Doc (avoid reparsing!)
                    triples = self.triple_segmenter.extract_triplets_from_doc(frag_info["doc"])

                    # Filter auxiliary-only triples if enabled
                    if self.filter_aux_edges:
                        from .openie.aux_filter import filter_triples

                        triples = filter_triples(
                            triples,
                            enable_aux_filter=self.filter_aux_edges,
                            keep_aux_if_alone=self.keep_aux_if_alone,
                        )

                    for triple in triples:
                        # Create triplet key for deduplication
                        key = (
                            triple.subject.lower(),
                            triple.relation.lower(),
                            triple.object.lower(),
                        )

                        if key in seen_triplets:
                            continue
                        seen_triplets.add(key)

                        # Create output triplet with metadata
                        triplet = Triplet(
                            subject=triple.subject,
                            relation=triple.relation,
                            object=triple.object,
                            confidence=frag_info["score"],
                            from_clause_split=frag_info["from_clause_split"],
                            from_entailment=frag_info["from_entailment"],
                            entailment_score=frag_info["score"],
                        )

                        all_triplets.append(triplet)

                except Exception as e:
                    logging.warning(
                        f"Triple extraction failed for fragment '{frag_info['text']}': {e}"
                    )

        # Sort by confidence
        all_triplets.sort(key=lambda t: t.confidence, reverse=True)

        # Apply quantity normalization to all triplets
        for triplet in all_triplets:
            triplet.subject = normalize_quantities(triplet.subject)
            triplet.relation = normalize_quantities(triplet.relation)
            triplet.object = normalize_quantities(triplet.object)

        logging.debug(
            f"Extracted {len(all_triplets)} unique triplets from {len(sentences)} sentences"
        )

        return all_triplets

    def extract_triplets_as_strings(self, text: str) -> list[str]:
        """
        Extract triplets as formatted strings (parenthesized format).

        Args:
            text: Input text

        Returns:
            List of triplets formatted as "(subject, relation, object)"
        """
        triplet_objects = self._extract_triplets_internal(text)
        return [str(triplet) for triplet in triplet_objects]

    def extract_batch(
        self, texts: list[str], batch_size: int = 32, progress: bool = True
    ) -> list[list[Triplet]]:
        """
        Extract triplets from multiple texts using efficient batching.

        This uses spaCy's nlp.pipe() for efficient batch processing, which is
        3-5x faster than processing texts individually.

        Args:
            texts: List of input texts to process
            batch_size: Number of texts to process in each batch (default: 32)
            progress: Show progress bar (requires tqdm)

        Returns:
            List of triplet lists, one per input text

        Example:
            >>> extractor = OpenIEExtractor()
            >>> texts = ["Sentence 1.", "Sentence 2.", "Sentence 3."]
            >>> results = extractor.extract_batch(texts)
            >>> for text, triplets in zip(texts, results):
            ...     print(f"{text}: {len(triplets)} triplets")
        """
        if not texts:
            return []

        # Parse all texts in batch using spaCy's efficient pipe()
        # This is much faster than parsing one at a time
        docs = list(self.nlp.pipe(texts, batch_size=batch_size))

        # Process each doc to extract triplets
        results = []
        iterator = zip(texts, docs, strict=True)
        if progress and HAS_TQDM:
            iterator = tqdm(iterator, total=len(texts), desc="Extracting triplets")

        for _text, doc in iterator:
            # Process each sentence in the doc
            sentences = list(doc.sents)
            all_triplets = []
            seen_triplets = set()

            for sent in sentences:
                sent_text = sent.text.strip()
                if not sent_text:
                    continue

                # Use the already-parsed sentence (as Doc)
                sent_doc = sent.as_doc()

                # Collect fragments
                fragments = []
                fragments.append(
                    {
                        "doc": sent_doc,
                        "text": sent_text,
                        "score": 1.0,
                        "from_clause_split": False,
                        "from_entailment": False,
                    }
                )

                # Stage 1: Clause Splitting
                if self.enable_clause_split and self.clause_splitter:
                    try:
                        clause_fragments = self.clause_splitter.split(sent_doc)
                        for frag in clause_fragments:
                            if frag.score < self.min_confidence:
                                continue
                            frag_text = str(frag)
                            if frag_text == sent_text:
                                continue
                            fragments.append(
                                {
                                    "doc": frag.doc,
                                    "text": frag_text,
                                    "score": frag.score,
                                    "from_clause_split": True,
                                    "from_entailment": False,
                                }
                            )
                    except Exception as e:
                        logging.warning(f"ClauseSplitter failed: {e}")

                # Stage 2: Forward Entailment
                if self.enable_entailment and self.forward_entailer:
                    try:
                        new_fragments = []
                        for frag_info in fragments:
                            entailed_fragments = self.forward_entailer.entail(
                                frag_info["doc"], truth_of_premise=True
                            )
                            for ent_frag in entailed_fragments:
                                if ent_frag.score < self.min_confidence:
                                    continue
                                ent_text = str(ent_frag)
                                if ent_text == frag_info["text"]:
                                    continue
                                new_fragments.append(
                                    {
                                        "doc": ent_frag.doc,
                                        "text": ent_text,
                                        "score": frag_info["score"] * ent_frag.score,
                                        "from_clause_split": frag_info["from_clause_split"],
                                        "from_entailment": True,
                                    }
                                )
                        fragments.extend(new_fragments)
                    except Exception as e:
                        logging.warning(f"ForwardEntailer failed: {e}")

                # Stage 3: Relation Triple Segmentation
                for frag_info in fragments:
                    try:
                        triples = self.triple_segmenter.extract_triplets_from_doc(frag_info["doc"])
                        for triple in triples:
                            key = (
                                triple.subject.lower(),
                                triple.relation.lower(),
                                triple.object.lower(),
                            )
                            if key in seen_triplets:
                                continue
                            seen_triplets.add(key)
                            triplet = Triplet(
                                subject=triple.subject,
                                relation=triple.relation,
                                object=triple.object,
                                confidence=frag_info["score"],
                                from_clause_split=frag_info["from_clause_split"],
                                from_entailment=frag_info["from_entailment"],
                                entailment_score=frag_info["score"],
                            )
                            all_triplets.append(triplet)
                    except Exception as e:
                        logging.warning(
                            f"Triple extraction failed for fragment '{frag_info['text']}': {e}"
                        )

            # Sort by confidence
            all_triplets.sort(key=lambda t: t.confidence, reverse=True)

            # Apply quantity normalization to all triplets
            for triplet in all_triplets:
                triplet.subject = normalize_quantities(triplet.subject)
                triplet.relation = normalize_quantities(triplet.relation)
                triplet.object = normalize_quantities(triplet.object)

            results.append(all_triplets)

        return results

    # Compatibility methods for different script interfaces
    def extract_claims(
        self,
        text: str,
        _source: str = "unknown",
        _credibility: float = 1.0,
        _metadata: dict[str, Any] = None,
    ):
        """
        Extract claims (triplets) from text.

        Compatibility method for scripts that expect extract_claims interface.
        Returns list of Claim-like objects (our Triplets have compatible attributes).

        Note: source, credibility, and metadata parameters are accepted for
        compatibility but not used in this implementation.
        """
        return self._extract_triplets_internal(text)

# coding: utf8
from __future__ import unicode_literals

import plac
import json
import spacy
import numpy
from pathlib import Path

from ..util import prints, ensure_path


@plac.annotations(
    lang=("model language", "positional", None, str),
    output_dir=("model output directory", "positional", None, Path),
    lexemes_loc=("location of JSONL-formatted lexical data", "positional",
                 None, Path),
    vectors_loc=("optional: location of vectors data, as numpy .npz",
                 "positional", None, str))
def make_vocab(cmd, lang, output_dir, lexemes_loc, vectors_loc=None):
    """Compile a vocabulary from a lexicon jsonl file and word vectors."""
    if not lexemes_loc.exists():
        prints(lexemes_loc, title="Can't find lexical data", exits=1)
    vectors_loc = ensure_path(vectors_loc)
    nlp = spacy.blank(lang)
    for word in nlp.vocab:
        word.rank = 0
    lex_added = 0
    vec_added = 0
    with lexemes_loc.open() as file_:
        for line in file_:
            if line.strip():
                attrs = json.loads(line)
                if 'settings' in attrs:
                    nlp.vocab.cfg.update(attrs['settings'])
                else:
                    lex = nlp.vocab[attrs['orth']]
                    lex.set_attrs(**attrs)
                    assert lex.rank == attrs['id']
                lex_added += 1
    if vectors_loc is not None:
        vector_data = numpy.load(open(vectors_loc, 'rb'))
        nlp.vocab.clear_vectors(width=vector_data.shape[1])
        for word in nlp.vocab:
            if word.rank:
                nlp.vocab.vectors.add(word.orth_, row=word.rank,
                                      vector=vector_data[word.rank])
                vec_added += 1
    if not output_dir.exists():
        output_dir.mkdir()
    nlp.to_disk(output_dir)
    prints("{} entries, {} vectors".format(lex_added, vec_added), output_dir,
           title="Sucessfully compiled vocab and vectors, and saved model")
    return nlp
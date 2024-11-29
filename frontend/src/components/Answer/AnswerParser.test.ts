import { cloneDeep } from 'lodash';
import { AskResponse, Citation } from '../../api'; // Ensure this path matches the location of your types

import { enumerateCitations, parseAnswer, ParsedAnswer } from './AnswerParser'; // Update the path accordingly

const sampleCitations: Citation[] = [
  {
    id: 'doc1',
    filepath: 'file1.pdf',
    part_index: undefined,
    content: '',
    title: null,
    url: null,
    metadata: null,
    chunk_id: null,
    reindex_id: null,
  },
  {
    id: 'doc2',
    filepath: 'file1.pdf',
    part_index: undefined,
    content: '',
    title: null,
    url: null,
    metadata: null,
    chunk_id: null,
    reindex_id: null,
  },
  {
    id: 'doc3',
    filepath: 'file2.pdf',
    part_index: undefined,
    content: '',
    title: null,
    url: null,
    metadata: null,
    chunk_id: null,
    reindex_id: null,
  },
];

const sampleAnswer: AskResponse = {
  answer: 'This is an example answer with citations [doc1] and [doc2].',
  citations: cloneDeep(sampleCitations),
  generated_chart: null,
};

describe('enumerateCitations', () => {
  it('assigns unique part_index based on filepath', () => {
    const results = enumerateCitations(cloneDeep(sampleCitations));
    expect(results[0].part_index).toEqual(1);
    expect(results[1].part_index).toEqual(2);
    expect(results[2].part_index).toEqual(1);
  });
});

describe('parseAnswer', () => {
  it('parses the answer correctly and reindexes citations', () => {
    const parsed: ParsedAnswer = parseAnswer(sampleAnswer);
    expect(parsed).not.toBeNull();
    expect(parsed?.citations.length).toEqual(2);
    expect(parsed?.citations[0].reindex_id).toEqual('1');
    expect(parsed?.citations[1].reindex_id).toEqual('2');
    expect(parsed?.markdownFormatText).toEqual('This is an example answer with citations ^1^ and ^2^ .');
  });

  it('returns null for invalid answer input', () => {
    const invalidAnswer: AskResponse = {
      answer: null,
      citations: [],
      generated_chart: null,
    };
    const parsed = parseAnswer(invalidAnswer);
    expect(parsed).toBeNull();
  });

  it('handles cases with no citations', () => {
    const noCitationAnswer: AskResponse = {
      answer: 'This is an example without citations.',
      citations: [],
      generated_chart: null,
    };
    const parsed = parseAnswer(noCitationAnswer);
    expect(parsed).not.toBeNull();
    expect(parsed?.citations.length).toEqual(0);
    expect(parsed?.markdownFormatText).toEqual('This is an example without citations.');
  });
});

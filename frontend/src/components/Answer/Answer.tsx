import { FormEvent, useContext, useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { nord } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Checkbox, DefaultButton, Dialog, FontIcon, Stack, Text } from '@fluentui/react';
import { useBoolean } from '@fluentui/react-hooks';
import { ThumbDislike20Filled, ThumbLike20Filled } from '@fluentui/react-icons';
import DOMPurify from 'dompurify';
import remarkGfm from 'remark-gfm';
import supersub from 'remark-supersub';

import { AskResponse, Citation, Feedback, historyMessageFeedback } from '../../api';
import { XSSAllowTags, XSSAllowAttributes } from '../../constants/sanatizeAllowables';
import { AppStateContext } from '../../state/AppProvider';

import { parseAnswer } from './AnswerParser';

import styles from './Answer.module.css';

interface Props {
  answer: AskResponse;
  onCitationClicked: (citedDocument: Citation) => void;
  onExectResultClicked: (answerId: string) => void;
}

export const Answer = ({ answer, onCitationClicked, onExectResultClicked }: Props) => {
  const [isRefAccordionOpen, { toggle: toggleIsRefAccordionOpen }] = useBoolean(false);
  const [feedbackState, setFeedbackState] = useState<Feedback | undefined>();
  const [isFeedbackDialogOpen, setIsFeedbackDialogOpen] = useState(false);
  const [showReportInappropriateFeedback, setShowReportInappropriateFeedback] = useState(false);
  const [negativeFeedbackList, setNegativeFeedbackList] = useState<Feedback[]>([]);

  const appStateContext = useContext(AppStateContext);
  const parsedAnswer = useMemo(() => parseAnswer(answer), [answer]);

  const FEEDBACK_ENABLED = appStateContext?.state.frontendSettings?.feedback_enabled;
  const SANITIZE_ANSWER = appStateContext?.state.frontendSettings?.sanitize_answer;

  const onLikeResponseClicked = async () => {
    if (!answer.message_id) return;

    const newFeedbackState =
      feedbackState === Feedback.Positive ? Feedback.Neutral : Feedback.Positive;
    setFeedbackState(newFeedbackState);
    appStateContext?.dispatch({
      type: 'SET_FEEDBACK_STATE',
      payload: { answerId: answer.message_id, feedback: newFeedbackState },
    });

    await historyMessageFeedback(answer.message_id, newFeedbackState);
  };

  const onDislikeResponseClicked = async () => {
    if (!answer.message_id) return;

    if (feedbackState === Feedback.Negative) {
      setFeedbackState(Feedback.Neutral);
      await historyMessageFeedback(answer.message_id, Feedback.Neutral);
    } else {
      setFeedbackState(Feedback.Negative);
      setIsFeedbackDialogOpen(true);
    }
  };

  const updateFeedbackList = (ev?: FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
    const selectedFeedback = (ev?.target as HTMLInputElement)?.id as Feedback;

    setNegativeFeedbackList((prev) =>
      checked ? [...prev, selectedFeedback] : prev.filter((f) => f !== selectedFeedback)
    );
  };

  const onSubmitNegativeFeedback = async () => {
    if (!answer.message_id) return;

    await historyMessageFeedback(answer.message_id, negativeFeedbackList.join(','));
    setIsFeedbackDialogOpen(false);
    setNegativeFeedbackList([]);
  };

  const components = {
    code({ node, ...props }: { node: any; [key: string]: any }) {
      const language = props.className?.match(/language-(\w+)/)?.[1];
      return (
        <SyntaxHighlighter style={nord} language={language} PreTag="div" {...props}>
          {node.children[0].value}
        </SyntaxHighlighter>
      );
    },
  };

  return (
    <Stack className={styles.answerContainer}>
      <ReactMarkdown
        linkTarget="_blank"
        remarkPlugins={[remarkGfm, supersub]}
        children={
          SANITIZE_ANSWER
            ? DOMPurify.sanitize(parsedAnswer?.markdownFormatText || '', {
                ALLOWED_TAGS: XSSAllowTags,
                ALLOWED_ATTR: XSSAllowAttributes,
              })
            : parsedAnswer?.markdownFormatText || ''
        }
        className={styles.answerText}
        components={components}
      />
      {FEEDBACK_ENABLED && (
        <Stack horizontal className={styles.feedbackContainer}>
          <ThumbLike20Filled
            onClick={onLikeResponseClicked}
            style={{
              color: feedbackState === Feedback.Positive ? 'green' : 'gray',
              cursor: 'pointer',
            }}
          />
          <ThumbDislike20Filled
            onClick={onDislikeResponseClicked}
            style={{
              color: feedbackState === Feedback.Negative ? 'red' : 'gray',
              cursor: 'pointer',
            }}
          />
        </Stack>
      )}
      {parsedAnswer?.citations && (
        <Stack className={styles.citationContainer}>
          {parsedAnswer.citations.map((citation, idx) => (
            <span
              key={idx}
              onClick={() => onCitationClicked(citation)}
              className={styles.citation}>
              [{idx + 1}] {citation.filepath}
            </span>
          ))}
        </Stack>
      )}
      <Dialog
        hidden={!isFeedbackDialogOpen}
        onDismiss={() => setIsFeedbackDialogOpen(false)}
        dialogContentProps={{ title: 'Submit Feedback' }}>
        <Stack tokens={{ childrenGap: 4 }}>
          {!showReportInappropriateFeedback ? (
            <>
              <Checkbox
                label="Citations are missing"
                id={Feedback.MissingCitation}
                onChange={updateFeedbackList}
              />
              <Checkbox
                label="Inaccurate response"
                id={Feedback.InaccurateOrIrrelevant}
                onChange={updateFeedbackList}
              />
              <Checkbox
                label="Out of scope"
                id={Feedback.OutOfScope}
                onChange={updateFeedbackList}
              />
            </>
          ) : (
            <Checkbox
              label="Inappropriate content"
              id={Feedback.OtherHarmful}
              onChange={updateFeedbackList}
            />
          )}
          <DefaultButton onClick={onSubmitNegativeFeedback}>Submit</DefaultButton>
        </Stack>
      </Dialog>
    </Stack>
  );
};

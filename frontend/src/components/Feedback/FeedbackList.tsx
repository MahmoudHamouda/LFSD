import React, { useEffect, useState } from 'react'
import { Feedback } from '../../api/feedback/feedbackModels'
import { getFeedback } from '../../api/feedback/feedbackApi'

export const FeedbackList: React.FC = () => {
  const [feedbackList, setFeedbackList] = useState<Feedback[]>([])

  useEffect(() => {
    (async () => {
      const feedback = await getFeedback()
      setFeedbackList(feedback)
    })()
  }, [])

  return (
    <ul>
      {feedbackList.map((fb) => (
        <li key={fb.messageId}>{fb.feedback}</li>
      ))}
    </ul>
  )
}

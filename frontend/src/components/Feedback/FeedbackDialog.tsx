import React, { useState } from 'react'
import { Feedback } from '../../api/feedback/feedbackModels'
import { submitFeedback } from '../../api/feedback/feedbackApi'

interface FeedbackDialogProps {
  isOpen: boolean
  onClose: () => void
}

export const FeedbackDialog: React.FC<FeedbackDialogProps> = ({ isOpen, onClose }) => {
  const [feedback, setFeedback] = useState<Feedback>({ messageId: '', userId: '', feedback: '' })

  const handleSubmit = async () => {
    await submitFeedback(feedback)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div>
      <textarea onChange={(e) => setFeedback({ ...feedback, feedback: e.target.value })} />
      <button onClick={handleSubmit}>Submit</button>
      <button onClick={onClose}>Cancel</button>
    </div>
  )
}

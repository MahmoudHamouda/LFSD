import { Feedback } from './feedbackModels'

export const submitFeedback = async (feedback: Feedback): Promise<Response> => {
  const response = await fetch('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(feedback),
  })
  return response
}

export const getFeedback = async (): Promise<Feedback[]> => {
  const response = await fetch('/api/feedback')
  const data = await response.json()
  return data.feedback
}

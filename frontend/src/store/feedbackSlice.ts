import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface FeedbackState {
  feedback: string[]
}

const initialState: FeedbackState = {
  feedback: [],
}

const feedbackSlice = createSlice({
  name: 'feedback',
  initialState,
  reducers: {
    addFeedback: (state, action: PayloadAction<string>) => {
      state.feedback.push(action.payload)
    },
  },
})

export const { addFeedback } = feedbackSlice.actions
export default feedbackSlice.reducer

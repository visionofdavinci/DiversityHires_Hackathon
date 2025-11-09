export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  actions?: AgentAction[]
  intents?: string[]
}

export interface AgentAction {
  type: 'suggestion' | 'data_fetch' | 'navigation' | 'filter'
  description: string
  data?: any
}
export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  time: string;
  loading?: boolean;
}

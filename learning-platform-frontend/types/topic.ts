export type TopicPracticeQuestion = {
  id: number;
  difficulty: number;
  question_text: string;
};

export type TopicDetail = {
  id: number;
  name: string;
  description: string;
  examples: string[];
  practice_questions: TopicPracticeQuestion[];
};

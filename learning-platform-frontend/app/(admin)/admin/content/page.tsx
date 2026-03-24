"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PageHeader from "@/components/layouts/PageHeader";
import { useToast } from "@/components/providers/ToastProvider";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import {
  createQuestion,
  createTopic,
  deleteQuestion,
  deleteTopic,
  exportQuestionsCsv,
  getQuestions,
  getTopics,
  importQuestionsCsv,
} from "@/services/topicService";

export default function AdminContentPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [topicName, setTopicName] = useState("");
  const [topicDescription, setTopicDescription] = useState("");
  const [topicId, setTopicId] = useState("1");
  const [questionText, setQuestionText] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState("");
  const [questionType, setQuestionType] = useState("multiple_choice");
  const [csvPayload, setCsvPayload] = useState("");

  const topicsQuery = useQuery({
    queryKey: ["admin", "content", "topics"],
    queryFn: getTopics,
  });
  const questionsQuery = useQuery({
    queryKey: ["admin", "content", "questions"],
    queryFn: () => getQuestions({ limit: 20, offset: 0 }),
  });

  const createTopicMutation = useMutation({
    mutationFn: createTopic,
    onSuccess: async () => {
      setTopicName("");
      setTopicDescription("");
      toast({ title: "Topic created", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "content", "topics"] });
    },
  });

  const createQuestionMutation = useMutation({
    mutationFn: createQuestion,
    onSuccess: async () => {
      setQuestionText("");
      setCorrectAnswer("");
      toast({ title: "Question created", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: ["admin", "content", "questions"] });
    },
  });

  const topics = useMemo(() => topicsQuery.data?.items ?? [], [topicsQuery.data?.items]);
  const questions = useMemo(() => questionsQuery.data?.items ?? [], [questionsQuery.data?.items]);

  const selectedTopicId = useMemo(
    () => Number(topicId || topics[0]?.id || 1),
    [topicId, topics],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Topic and question management"
        description="Create topics, add questions, and use import/export helpers against the topic APIs."
      />

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <SurfaceCard title="Create topic" description="Add a new topic to the tenant content graph.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createTopicMutation.mutate({ name: topicName, description: topicDescription });
            }}
          >
            <Input value={topicName} onChange={(event) => setTopicName(event.target.value)} placeholder="Topic name" required />
            <Input value={topicDescription} onChange={(event) => setTopicDescription(event.target.value)} placeholder="Topic description" required />
            <Button type="submit" disabled={createTopicMutation.isPending}>
              Create topic
            </Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Topic inventory" description="Existing tenant topics returned by `/topics`.">
          <div className="grid gap-3 md:grid-cols-2">
            {topics.map((topic) => (
              <div
                key={topic.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{topic.name}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-400">{topic.description}</p>
                  </div>
                  <Button
                    variant="ghost"
                    className="h-auto px-3 py-2"
                    onClick={() => deleteTopic(topic.id).then(async () => {
                      toast({ title: "Topic deleted", variant: "success" });
                      await queryClient.invalidateQueries({ queryKey: ["admin", "content", "topics"] });
                    })}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SurfaceCard title="Create question" description="Attach a new practice question to a topic.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createQuestionMutation.mutate({
                topic_id: selectedTopicId,
                difficulty: 2,
                question_type: questionType,
                question_text: questionText,
                correct_answer: correctAnswer,
                accepted_answers: [correctAnswer],
                answer_options: questionType === "multiple_choice" ? [correctAnswer] : [],
              });
            }}
          >
            <Select value={topicId} onChange={(event) => setTopicId(event.target.value)}>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.name}
                </option>
              ))}
            </Select>
            <Select value={questionType} onChange={(event) => setQuestionType(event.target.value)}>
              <option value="multiple_choice">multiple_choice</option>
              <option value="short_text">short_text</option>
            </Select>
            <Input value={questionText} onChange={(event) => setQuestionText(event.target.value)} placeholder="Question text" required />
            <Input value={correctAnswer} onChange={(event) => setCorrectAnswer(event.target.value)} placeholder="Correct answer" required />
            <Button type="submit">Create question</Button>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Questions" description="Recent questions from `/topics/questions` with quick delete actions.">
          <div className="space-y-3">
            {questions.map((question) => (
              <div
                key={question.id}
                className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{question.question_text}</p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      Topic #{question.topic_id} • {question.question_type}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    className="h-auto px-3 py-2"
                    onClick={() => deleteQuestion(question.id).then(async () => {
                      toast({ title: "Question deleted", variant: "success" });
                      await queryClient.invalidateQueries({ queryKey: ["admin", "content", "questions"] });
                    })}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="CSV import / export" description="Use backend CSV endpoints for bulk content workflows.">
        <div className="grid gap-4 xl:grid-cols-[1fr_auto_auto] xl:items-start">
          <textarea
            value={csvPayload}
            onChange={(event) => setCsvPayload(event.target.value)}
            rows={6}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            placeholder="Paste CSV payload here"
          />
          <Button
            onClick={() =>
              importQuestionsCsv(csvPayload).then(() => {
                toast({ title: "CSV imported", variant: "success" });
                queryClient.invalidateQueries({ queryKey: ["admin", "content", "questions"] });
              })
            }
          >
            Import CSV
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              exportQuestionsCsv().then((content) => {
                navigator.clipboard.writeText(content);
                toast({ title: "CSV copied", description: "Exported question CSV copied to clipboard.", variant: "success" });
              })
            }
          >
            Export CSV
          </Button>
        </div>
      </SurfaceCard>
    </div>
  );
}

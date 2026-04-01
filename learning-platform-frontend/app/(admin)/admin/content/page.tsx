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
  updateQuestion,
  updateTopic,
} from "@/services/topicService";

export default function AdminContentPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [topicName, setTopicName] = useState("");
  const [topicDescription, setTopicDescription] = useState("");
  const [editingTopicId, setEditingTopicId] = useState<number | null>(null);
  const [topicId, setTopicId] = useState("1");
  const [questionText, setQuestionText] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState("");
  const [acceptedAnswers, setAcceptedAnswers] = useState("");
  const [answerOptions, setAnswerOptions] = useState("");
  const [questionType, setQuestionType] = useState("multiple_choice");
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null);
  const [csvPayload, setCsvPayload] = useState("");

  const topicsQuery = useQuery({
    queryKey: ["admin", "content", "topics"],
    queryFn: getTopics,
  });
  const questionsQuery = useQuery({
    queryKey: ["admin", "content", "questions"],
    queryFn: () => getQuestions({ limit: 50, offset: 0 }),
  });

  const topics = useMemo(() => topicsQuery.data?.items ?? [], [topicsQuery.data?.items]);
  const questions = useMemo(() => questionsQuery.data?.items ?? [], [questionsQuery.data?.items]);
  const selectedTopicId = useMemo(() => Number(topicId || topics[0]?.id || 1), [topicId, topics]);

  const refreshTopics = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "content", "topics"] });
  };

  const refreshQuestions = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "content", "questions"] });
  };

  const createTopicMutation = useMutation({
    mutationFn: createTopic,
    onSuccess: async () => {
      setTopicName("");
      setTopicDescription("");
      toast({ title: "Topic created", variant: "success" });
      await refreshTopics();
    },
  });

  const createQuestionMutation = useMutation({
    mutationFn: createQuestion,
    onSuccess: async () => {
      resetQuestionForm();
      toast({ title: "Question created", variant: "success" });
      await refreshQuestions();
    },
  });

  function resetQuestionForm(): void {
    setEditingQuestionId(null);
    setQuestionText("");
    setCorrectAnswer("");
    setAcceptedAnswers("");
    setAnswerOptions("");
    setQuestionType("multiple_choice");
  }

  function parseCsvField(value: string): string[] {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Content operations"
        description="Manage tenant topics, curate question banks, and maintain accepted answers and choice options without leaving the admin workspace."
      />

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <SurfaceCard title="Topic editor" description="Create or update topic records used across diagnostics, graphs, and roadmaps.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              if (editingTopicId) {
                updateTopic(editingTopicId, { name: topicName, description: topicDescription }).then(async () => {
                  setEditingTopicId(null);
                  setTopicName("");
                  setTopicDescription("");
                  toast({ title: "Topic updated", variant: "success" });
                  await refreshTopics();
                });
                return;
              }
              createTopicMutation.mutate({ name: topicName, description: topicDescription });
            }}
          >
            <Input value={topicName} onChange={(event) => setTopicName(event.target.value)} placeholder="Topic name" required />
            <Input value={topicDescription} onChange={(event) => setTopicDescription(event.target.value)} placeholder="Topic description" required />
            <div className="flex gap-3">
              <Button type="submit" disabled={createTopicMutation.isPending}>
                {editingTopicId ? "Update topic" : "Create topic"}
              </Button>
              {editingTopicId ? (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setEditingTopicId(null);
                    setTopicName("");
                    setTopicDescription("");
                  }}
                >
                  Cancel
                </Button>
              ) : null}
            </div>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Topic inventory" description="Use quick edit actions to keep the tenant knowledge graph clean.">
          <div className="grid gap-3 md:grid-cols-2">
            {topics.map((topic) => (
              <div key={topic.id} className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{topic.name}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-400">{topic.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      className="h-auto px-3 py-2"
                      onClick={() => {
                        setEditingTopicId(topic.id);
                        setTopicName(topic.name);
                        setTopicDescription(topic.description);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      className="h-auto px-3 py-2"
                      onClick={() => deleteTopic(topic.id).then(async () => {
                        toast({ title: "Topic deleted", variant: "success" });
                        await refreshTopics();
                      })}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SurfaceCard title="Question and answer editor" description="Create or update the full answer model: prompt, canonical answer, aliases, and multiple-choice options.">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              const payload = {
                topic_id: selectedTopicId,
                difficulty: 2,
                question_type: questionType,
                question_text: questionText,
                correct_answer: correctAnswer,
                accepted_answers: parseCsvField(acceptedAnswers),
                answer_options: questionType === "multiple_choice" ? parseCsvField(answerOptions) : [],
              };
              if (editingQuestionId) {
                updateQuestion(editingQuestionId, payload).then(async () => {
                  resetQuestionForm();
                  toast({ title: "Question updated", variant: "success" });
                  await refreshQuestions();
                });
                return;
              }
              createQuestionMutation.mutate(payload);
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
            <Input value={correctAnswer} onChange={(event) => setCorrectAnswer(event.target.value)} placeholder="Canonical answer" required />
            <Input value={acceptedAnswers} onChange={(event) => setAcceptedAnswers(event.target.value)} placeholder="Accepted answers, comma separated" />
            {questionType === "multiple_choice" ? (
              <Input value={answerOptions} onChange={(event) => setAnswerOptions(event.target.value)} placeholder="Choice options, comma separated" required />
            ) : null}
            <div className="flex gap-3">
              <Button type="submit">{editingQuestionId ? "Update question" : "Create question"}</Button>
              {editingQuestionId ? (
                <Button type="button" variant="ghost" onClick={resetQuestionForm}>
                  Cancel
                </Button>
              ) : null}
            </div>
          </form>
        </SurfaceCard>

        <SurfaceCard title="Question bank" description="Review current answer keys and edit or remove stale items.">
          <div className="space-y-3">
            {questions.map((question) => (
              <div key={question.id} className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{question.question_text}</p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      Topic #{question.topic_id} • {question.question_type}
                    </p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Accepted: {question.accepted_answers.join(", ") || "None"}</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Options: {question.answer_options.join(", ") || "None"}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      className="h-auto px-3 py-2"
                      onClick={() => {
                        setEditingQuestionId(question.id);
                        setTopicId(String(question.topic_id));
                        setQuestionType(question.question_type);
                        setQuestionText(question.question_text);
                        setCorrectAnswer(question.correct_answer);
                        setAcceptedAnswers(question.accepted_answers.join(", "));
                        setAnswerOptions(question.answer_options.join(", "));
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      className="h-auto px-3 py-2"
                      onClick={() => deleteQuestion(question.id).then(async () => {
                        toast({ title: "Question deleted", variant: "success" });
                        await refreshQuestions();
                      })}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Bulk import and export" description="Use CSV endpoints for larger content operations or migrations.">
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
              importQuestionsCsv(csvPayload).then(async () => {
                toast({ title: "CSV imported", variant: "success" });
                await refreshQuestions();
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

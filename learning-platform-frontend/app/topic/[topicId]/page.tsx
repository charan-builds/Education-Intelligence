import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function TopicLearningPage({
  params,
}: {
  params: Promise<{ topicId: string }>;
}) {
  const { topicId } = await params;
  redirect(`/student/topics/${topicId}`);
}

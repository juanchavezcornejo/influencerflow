import { SessionDetail } from "./SessionDetail.client";

export const metadata = {
  title: "Session — InfluencerFlow",
};

export default async function SessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <SessionDetail sessionId={id} />;
}

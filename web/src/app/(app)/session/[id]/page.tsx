import { SessionDetail } from "./SessionDetail.client";

export const metadata = {
  title: "Session — InfluencerFlow",
};

export default async function SessionPage({ params }: { params: { id: string } }) {
  return <SessionDetail sessionId={params.id} />;
}

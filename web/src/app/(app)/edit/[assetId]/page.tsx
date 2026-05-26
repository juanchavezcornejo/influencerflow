import { EditView } from "./EditView.client";

interface Props {
  params: Promise<{ assetId: string }>;
}

export default async function EditPage({ params }: Props) {
  const { assetId } = await params;
  return <EditView assetId={assetId} />;
}

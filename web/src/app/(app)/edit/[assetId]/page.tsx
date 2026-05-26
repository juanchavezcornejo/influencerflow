import { EditView } from "./EditView.client";

interface Props {
  params: { assetId: string };
}

export default function EditPage({ params }: Props) {
  return <EditView assetId={params.assetId} />;
}

type Props = {
  message: string;
};

export default function EmptyState({ message }: Props) {
  return <p>{message}</p>;
}
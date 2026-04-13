type Props = {
  message: string;
};

export default function ErrorState({ message }: Props) {
  return <p>Error: {message}</p>;
}
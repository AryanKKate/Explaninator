import "./globals.css";

export const metadata = {
  title: "Explaninator",
  description: "AI Tutor powered by CrewAI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-bg text-text min-h-screen">
        {children}
      </body>
    </html>
  );
}

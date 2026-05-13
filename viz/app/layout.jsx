export const metadata = {
  title: "The Amnesiac — Run Replay",
  description: "Step-by-step replay of an Amnesiac agent run",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#0f1117", color: "#e2e8f0", fontFamily: "monospace" }}>
        {children}
      </body>
    </html>
  );
}

/**
 * Render the public marketing landing page for JobFit AI.
 *
 * @returns The root JSX element representing the landing page.
 */

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-gray-900">JobFit AI</h1>
        <p className="mt-4 text-xl text-gray-600">
          Intelligent Resume Optimization Agent
        </p>
        <p className="mt-2 text-gray-500">
          Upload your resume, paste a job description, and let AI optimize your
          application.
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <a
            href="/login"
            className="rounded-lg bg-blue-600 px-6 py-3 text-white font-medium hover:bg-blue-700"
          >
            Sign In
          </a>
          <a
            href="/register"
            className="rounded-lg border border-gray-300 px-6 py-3 text-gray-700 font-medium hover:bg-gray-100"
          >
            Get Started
          </a>
        </div>
      </div>
    </main>
  );
}
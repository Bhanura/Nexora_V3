import { useState, useEffect } from "react";
import { Clock, CheckCircle, XCircle, Loader2, Globe } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardContent } from "../ui/Card";

export default function CrawlJobList() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const data = await authenticatedFetch("/ingest/jobs?limit=10");
      setJobs(data.jobs);
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "running":
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  if (loading) {
    return <div className="text-center py-4">Loading crawl history...</div>;
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-gray-500">
          <Globe className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No crawl jobs yet. Start by crawling a website!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Crawl Jobs</h3>
        <div className="space-y-3 custom-scrollbar max-h-96 overflow-y-auto">
          {jobs.map((job) => (
            <div
              key={job._id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 ">
                {getStatusIcon(job.status)}
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{job.url}</p>
                  <p className="text-sm text-gray-500">
                    {job.status === "completed"
                      ? `${job.pages_crawled} pages, ${job.documents_created} docs`
                      : job.status === "failed"
                      ? `Error: ${job.error_message || "Unknown"}`
                      : "In progress..."}
                  </p>
                </div>
              </div>
              <div className="text-sm text-gray-400">
                {new Date(job.started_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
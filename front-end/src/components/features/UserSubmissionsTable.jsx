import { useState, useEffect } from "react";
import { Trash2, Download, RefreshCw } from "lucide-react";
import { Card, CardHeader, CardContent } from "../ui/Card";

export default function UserSubmissionsTable() {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [fieldConfig, setFieldConfig] = useState({});

  useEffect(() => {
    fetchDataCollectionConfig();
    fetchSubmissions();
  }, [page]);

  const fetchDataCollectionConfig = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/settings/data-collection", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Create a map of field_id -> label
        const fieldMap = {};
        (data.custom_fields || []).forEach(field => {
          fieldMap[field.field_id] = field.label;
        });
        setFieldConfig(fieldMap);
      }
    } catch (err) {
      console.error("Failed to fetch field config:", err);
    }
  };

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(
        `/api/user-data/submissions?page=${page}&page_size=${pageSize}`,
        { headers: { "Authorization": `Bearer ${token}` } }
      );

      if (res.ok) {
        const data = await res.json();
        setSubmissions(data.submissions || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error("Failed to fetch submissions:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteSubmission = async (submissionId) => {
    if (!confirm("Are you sure you want to delete this submission?")) {
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/user-data/submissions/${submissionId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        fetchSubmissions(); // Refresh list
      } else {
        alert("Failed to delete submission");
      }
    } catch (err) {
      alert("Network error");
    }
  };

  const exportToCSV = () => {
    if (submissions.length === 0) {
      alert("No data to export");
      return;
    }

    // Get all unique field IDs
    const allFieldIds = new Set();
    submissions.forEach(sub => {
      Object.keys(sub.submitted_data).forEach(key => allFieldIds.add(key));
    });
    const fieldIds = Array.from(allFieldIds);

    // Map field IDs to labels (or use ID if label not found)
    const fieldLabels = fieldIds.map(id => fieldConfig[id] || id);

    // Build CSV
    const headers = ["Submission ID", "Session ID", "Submitted At", ...fieldLabels];
    const rows = submissions.map(sub => {
      const row = [
        sub.submission_id,
        sub.session_id,
        new Date(sub.submitted_at).toLocaleString(),
        ...fieldIds.map(fieldId => sub.submitted_data[fieldId] || "")
      ];
      return row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",");
    });

    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `submissions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading && submissions.length === 0) {
    return (
      <Card>
        <CardContent>
          <div className="text-center py-8">Loading submissions...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-lg">User Data Submissions</h3>
            <p className="text-sm text-gray-500">{total} total submissions</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchSubmissions}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded transition text-sm"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              onClick={exportToCSV}
              disabled={submissions.length === 0}
              className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white hover:bg-green-700 rounded transition text-sm disabled:bg-gray-400"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {submissions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No submissions yet</p>
            <p className="text-sm">User data will appear here when visitors submit the form in your widget.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-700">Submitted At</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-700">Session ID</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-700">Data</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {submissions.map(sub => (
                  <tr key={sub.submission_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-700">
                      {new Date(sub.submitted_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-gray-600 font-mono text-xs">
                      {sub.session_id.substring(0, 12)}...
                    </td>
                    <td className="px-4 py-3">
                      <div className="space-y-1">
                        {Object.entries(sub.submitted_data).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-medium text-gray-700">{fieldConfig[key] || key}:</span>{" "}
                            <span className="text-gray-600">{value}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => deleteSubmission(sub.submission_id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {total > pageSize && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 text-sm"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * pageSize >= total}
                    className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 text-sm"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

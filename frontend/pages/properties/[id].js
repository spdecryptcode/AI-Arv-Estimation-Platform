import React from 'react';
import { useRouter } from 'next/router';
import useSWR from 'swr';
import axios from 'axios';

const fetcher = (url) => axios.get(url).then((res) => res.data);

export default function PropertyPage() {
  const router = useRouter();
  const { id } = router.query;
  const base = process.env.NEXT_PUBLIC_API_BASE;
  const { data, error } = useSWR(id ? `${base}/properties/${id}` : null, fetcher);
  const { data: arvData } = useSWR(
    id ? `${base}/properties/${id}/arv` : null,
    fetcher
  );

  if (error) return <div>Error loading</div>;
  if (!data) return <div>Loading…</div>;

  // report state
  const [reportTask, setReportTask] = React.useState(null);
  const [reportStatus, setReportStatus] = React.useState(null);

  React.useEffect(() => {
    let timer;
    if (reportTask) {
      const check = async () => {
        const resp = await fetch(`${base}/properties/${id}/report_status/${reportTask}`,
          { headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` } }
        );
        const js = await resp.json();
        setReportStatus(js);
        if (!js.download_path) {
          timer = setTimeout(check, 2000);
        }
      };
      check();
    }
    return () => clearTimeout(timer);
  }, [reportTask, id, base]);

  const startReport = async () => {
    const resp = await fetch(`${base}/properties/${id}/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
      body: JSON.stringify({}),
    });
    const js = await resp.json();
    setReportTask(js.task_id);
    setReportStatus(null);
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-2">{data.address}</h1>
      <p>ID: {data.id}</p>
      <p>Created: {data.created_at}</p>
      <p>Updated: {data.updated_at}</p>
      {arvData && (
        <p>
          ARV range: {arvData.min} - {arvData.max}
        </p>
      )}
      <div className="mt-4">
        <button onClick={startReport} className="px-2 py-1 bg-blue-500 text-white rounded">
          {reportTask ? 'Refresh Report Status' : 'Generate Report'}
        </button>
      </div>
      {reportStatus && (
        <div className="mt-2">
          <p>Task {reportStatus.task_id}: {reportStatus.state}</p>
          {reportStatus.download_path && (
            <p>
              <a href={reportStatus.download_path} className="text-green-600 underline" target="_blank" rel="noopener noreferrer">
                Download report
              </a>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import React from 'react';
import useSWR from 'swr';
import axios from 'axios';
import Link from 'next/link';

const fetcher = (url) => axios.get(url).then((res) => res.data);

export default function SearchPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  const [query, setQuery] = React.useState("Test");
  const { data, error } = useSWR(
    query ? `${base}/properties/search?q=${encodeURIComponent(query)}` : null,
    fetcher
  );

  if (error) return <div>Error loading</div>;
  if (!data) return <div>Loading…</div>;

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">Property Search (demo)</h1>
        {!localStorage.getItem('token') && (
          <Link href="/login" className="text-blue-600 underline">
            Login
          </Link>
        )}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
        }}
        className="mb-4"
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter address or ID..."
          className="border p-2 w-full"
        />
      </form>
      {data && data.hits && (
        <ul>
          {data.hits.map((h) => (
            <li key={h.id}>
              <Link href={`/properties/${h.id}`} className="text-blue-600 underline">
                {h.address}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

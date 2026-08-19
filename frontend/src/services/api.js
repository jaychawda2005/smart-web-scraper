/**
 * api.js — SmartScrape API service
 * All backend communication goes through this file.
 * Base URL is defined once here.
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Scrape a URL with the given extraction options.
 * @param {string} url
 * @param {object} options - e.g. { page_info: true, headings: true, ... }
 * @param {boolean} renderJs - when true, uses headless Chromium for JS-rendered pages
 */
export async function scrapeUrl(url, options, renderJs = false) {
  const res = await api.post('/api/scrape', { url, options, render_js: renderJs });
  return res.data;
}

/**
 * Fetch recent scraping history.
 * @param {number} limit
 */
export async function getHistory(limit = 50) {
  const res = await api.get('/api/history', { params: { limit } });
  return res.data;
}

/**
 * Delete a single history record.
 * @param {number} id
 */
export async function deleteHistoryItem(id) {
  const res = await api.delete(`/api/history/${id}`);
  return res.data;
}

/**
 * Trigger a JSON file download of the last scrape result.
 */
export function exportJson() {
  window.location.href = `${BASE_URL}/api/export/json`;
}

/**
 * Trigger a CSV file download of the last scrape result.
 */
export function exportCsv() {
  window.location.href = `${BASE_URL}/api/export/csv`;
}

/**
 * Trigger an Excel file download of the last scrape result.
 */
export function exportExcel() {
  window.location.href = `${BASE_URL}/api/export/excel`;
}

export default api;

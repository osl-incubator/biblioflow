import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "../App";

interface MockResponseInit {
  status?: number;
  ok?: boolean;
}

function jsonResponse(payload: unknown, init: MockResponseInit = {}): Response {
  return {
    ok: init.ok ?? (init.status ?? 200) < 400,
    status: init.status ?? 200,
    json: () => Promise.resolve(payload),
  } as Response;
}

function renderProjectUpload() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/projects/project-1/upload"]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("remote source import", () => {
  it("shows a not found state when the project cannot be loaded", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse(
          { error: { message: "Project not found" } },
          { status: 404 },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    expect(await screen.findByText("Project not found")).toBeDefined();
    expect(
      screen.getByRole("link", { name: /Back to projects/i }),
    ).toBeDefined();
  });

  it("submits a PMC import request and shows the imported dataset", async () => {
    const requestBodies: unknown[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Remote project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (url.endsWith("/projects/project-1/sources/import")) {
        requestBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              dataset_id: "dataset-1",
              created_at: "2026-01-01T00:00:00Z",
              upload_ids: [],
              records: [{ title: "PMC record" }],
              warnings: [],
              metadata: { remote_source: "pmc", query: "open science" },
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    await screen.findByRole("heading", { name: /Search PubMed or PMC/i });
    await userEvent.selectOptions(screen.getByLabelText("Source"), "pmc");
    await userEvent.clear(screen.getByLabelText("Limit"));
    await userEvent.type(screen.getByLabelText("Limit"), "12");
    await userEvent.type(
      screen.getByLabelText("Contact email"),
      "r@example.org",
    );
    await userEvent.type(screen.getByLabelText("NCBI API key"), "secret-token");
    await userEvent.clear(screen.getByLabelText("Tool name"));
    await userEvent.type(screen.getByLabelText("Dataset name"), "PMC import");
    await userEvent.type(screen.getByLabelText("Query"), "open science");
    await userEvent.click(
      screen.getByRole("button", { name: /Search and import records/i }),
    );

    await waitFor(() => expect(requestBodies).toHaveLength(1));
    expect(requestBodies[0]).toEqual({
      source: "pmc",
      query: "open science",
      limit: 12,
      email: "r@example.org",
      api_key: "secret-token",
      tool: "biblioflow-web",
      name: "PMC import",
    });
    expect(await screen.findByText(/Imported/i)).toBeDefined();
    expect(screen.getByText("dataset-1")).toBeDefined();
    expect(
      (screen.getByLabelText("NCBI API key") as HTMLInputElement).value,
    ).toBe("");
    expect(
      screen.getAllByRole("link", { name: /Go to dashboard/i }).length,
    ).toBeGreaterThan(0);
  });

  it("displays backend remote import errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Remote project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({ data: [], warnings: [], metadata: {} }),
        );
      }
      if (url.endsWith("/projects/project-1/sources/import")) {
        return Promise.resolve(
          jsonResponse(
            {
              error: {
                message:
                  "Pass an email or set BIBLIOFLOW_NCBI_EMAIL on the backend.",
              },
            },
            { status: 400 },
          ),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    await screen.findByRole("heading", { name: /Search PubMed or PMC/i });
    await userEvent.type(screen.getByLabelText("Query"), "bibliometrics");
    await userEvent.click(
      screen.getByRole("button", { name: /Search and import records/i }),
    );

    expect((await screen.findByRole("alert")).textContent).toMatch(
      /BIBLIOFLOW_NCBI_EMAIL/i,
    );
  });

  it("renders upload size formats and ignores empty file events", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Size project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-kb",
                filename: "medium.ris",
                content_type: "application/x-research-info-systems",
                size: 2048,
                created_at: "2026-01-01T00:00:00Z",
              },
              {
                upload_id: "upload-mb",
                filename: "large.bib",
                content_type: "application/x-bibtex",
                size: 2 * 1024 * 1024,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = renderProjectUpload();

    expect(await screen.findByText("2.0 KB")).toBeDefined();
    expect(await screen.findByText("2.0 MB")).toBeDefined();

    const dropzone = screen
      .getByText("Upload bibliographic files")
      .closest("label");
    expect(dropzone).not.toBeNull();
    fireEvent.dragOver(dropzone as HTMLLabelElement);
    fireEvent.drop(dropzone as HTMLLabelElement, {
      dataTransfer: { files: [] },
    });

    const input =
      container.querySelector<HTMLInputElement>("input[type='file']");
    expect(input).not.toBeNull();
    fireEvent.change(input as HTMLInputElement, {
      target: { files: null },
    });
    expect(screen.queryByText("Ready to upload")).toBeNull();
  });

  it("displays upload list errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Upload errors",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads")) {
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Unable to load uploads." } },
            { status: 500 },
          ),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    expect((await screen.findByRole("alert")).textContent).toMatch(
      /Unable to load uploads\./i,
    );
  });

  it("displays upload mutation, delete, and dataset load errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Mutation errors",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "GET") {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-1",
                filename: "minimal.json",
                content_type: "application/json",
                size: 42,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "POST") {
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Upload failed" } },
            { status: 400 },
          ),
        );
      }
      if (
        url.endsWith("/projects/project-1/uploads/upload-1") &&
        method === "DELETE"
      ) {
        return Promise.resolve(
          jsonResponse(
            { error: { message: "Delete failed" } },
            { status: 500 },
          ),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/load")) {
        return Promise.resolve(
          jsonResponse({ error: { message: "Load failed" } }, { status: 422 }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = renderProjectUpload();

    await screen.findByText("minimal.json");
    await userEvent.click(screen.getByRole("button", { name: /Delete/i }));
    expect(await screen.findByText("Delete failed")).toBeDefined();

    const input =
      container.querySelector<HTMLInputElement>("input[type='file']");
    expect(input).not.toBeNull();
    await userEvent.upload(
      input as HTMLInputElement,
      new File(["{}"], "records.json", { type: "application/json" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /Upload selected files/i }),
    );
    expect(await screen.findByText("Upload failed")).toBeDefined();

    await userEvent.click(
      screen.getByRole("button", { name: /Load selected uploads/i }),
    );
    expect(await screen.findByText("Load failed")).toBeDefined();
  });

  it("uploads files and loads selected uploads", async () => {
    const uploadedFiles: string[] = [];
    const loadBodies: unknown[] = [];
    const deletedUploadIds: string[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Upload project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "GET") {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-1",
                filename: "minimal.json",
                content_type: "application/json",
                size: 42,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "POST") {
        const form = init?.body as FormData;
        uploadedFiles.push((form.get("files") as File).name);
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-2",
                filename: "records.json",
                content_type: "application/json",
                size: 2,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (
        url.endsWith("/projects/project-1/uploads/upload-1") &&
        method === "DELETE"
      ) {
        deletedUploadIds.push("upload-1");
        return Promise.resolve(
          jsonResponse({
            data: { deleted: true },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/load")) {
        loadBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              dataset_id: "dataset-2",
              created_at: "2026-01-01T00:00:00Z",
              upload_ids: ["upload-1", "upload-2"],
              records: [{ title: "Loaded record" }],
              warnings: [],
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = renderProjectUpload();

    await screen.findByText("minimal.json");
    const checkbox = screen.getByLabelText("Select minimal.json");
    await userEvent.click(checkbox);
    await userEvent.click(checkbox);
    await userEvent.click(screen.getByRole("button", { name: /Delete/i }));
    await waitFor(() => expect(deletedUploadIds).toEqual(["upload-1"]));

    await userEvent.selectOptions(screen.getByLabelText("Provider"), "wos");
    await userEvent.selectOptions(screen.getByLabelText("Format"), "ris");

    const input =
      container.querySelector<HTMLInputElement>("input[type='file']");
    expect(input).not.toBeNull();
    const dropzone = screen
      .getByText("Upload bibliographic files")
      .closest("label");
    expect(dropzone).not.toBeNull();
    fireEvent.drop(dropzone as HTMLLabelElement, {
      dataTransfer: {
        files: [new File(["{}"], "dropped.json", { type: "application/json" })],
      },
    });
    expect(await screen.findByText(/dropped\.json · 2 B/i)).toBeDefined();
    await userEvent.click(screen.getByRole("button", { name: /Clear/i }));
    expect(screen.queryByText(/dropped\.json · 2 B/i)).toBeNull();

    await userEvent.upload(
      input as HTMLInputElement,
      new File(["{}"], "records.json", { type: "application/json" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /Upload selected files/i }),
    );
    await waitFor(() => expect(uploadedFiles).toEqual(["records.json"]));

    await userEvent.click(
      screen.getByRole("button", { name: /Load selected uploads/i }),
    );
    await waitFor(() =>
      expect(loadBodies).toEqual([
        {
          upload_ids: ["upload-2"],
          provider: "wos",
          format: "ris",
        },
      ]),
    );
  });

  it("routes to validation when loading a dataset returns warnings", async () => {
    const loadBodies: unknown[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/projects/project-1")) {
        return Promise.resolve(
          jsonResponse({
            data: {
              project_id: "project-1",
              name: "Warning project",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              active_dataset_id: null,
              source_files: [],
              datasets: [],
              filters: {},
              metadata: {},
            },
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/uploads") && method === "GET") {
        return Promise.resolve(
          jsonResponse({
            data: [
              {
                upload_id: "upload-1",
                filename: "warning.json",
                content_type: "application/json",
                size: 42,
                created_at: "2026-01-01T00:00:00Z",
              },
            ],
            warnings: [],
            metadata: {},
          }),
        );
      }
      if (url.endsWith("/projects/project-1/datasets/load")) {
        loadBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve(
          jsonResponse({
            data: {
              dataset_id: "dataset-warning",
              created_at: "2026-01-01T00:00:00Z",
              upload_ids: ["upload-1"],
              records: [{ title: "Warning record" }],
              warnings: [{ message: "Review imported metadata" }],
              metadata: {},
            },
            warnings: [{ message: "Review imported metadata" }],
            metadata: {},
          }),
        );
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProjectUpload();

    await screen.findByText("warning.json");
    await userEvent.click(
      screen.getByRole("button", { name: /Load selected uploads/i }),
    );
    await waitFor(() =>
      expect(loadBodies).toEqual([
        { upload_ids: ["upload-1"], provider: "auto", format: "auto" },
      ]),
    );
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "../App";
import type { Project } from "../api/types";

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

function stubApi(projects: Project[] = []) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/health")) {
      return Promise.resolve(
        jsonResponse({
          service: "biblioflow-web",
          status: "ok",
          version: "0.1.0",
          biblioflow_version: "0.1.0",
        }),
      );
    }
    if (url.endsWith("/projects")) {
      return Promise.resolve(jsonResponse({ data: projects }));
    }
    return Promise.resolve(
      jsonResponse({ error: { message: "Not found" } }, { status: 404 }),
    );
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderApp(initialEntries = ["/"]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const existingProject: Project = {
  project_id: "project-1",
  name: "Evidence synthesis review",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  active_dataset_id: "dataset-1",
};

describe("App", () => {
  it("renders the home page", () => {
    stubApi();
    renderApp();
    expect(
      screen.getByRole("heading", {
        name: /Bibliometric analysis in the browser/i,
      }),
    ).toBeDefined();
  });

  it("shows existing projects from the home page", async () => {
    stubApi([existingProject]);
    renderApp();

    const projectAccess = screen.getByRole("region", {
      name: /Project access/i,
    });
    expect(
      await within(projectAccess).findByText("Evidence synthesis review"),
    ).toBeDefined();
    expect(
      (
        within(projectAccess).getByRole("link", {
          name: /Open project/i,
        }) as HTMLAnchorElement
      ).getAttribute("href"),
    ).toBe("/projects/project-1/dashboard/overview");
  });

  it("shows an explicit projects selector in the sidebar menu", () => {
    stubApi();
    renderApp();

    expect(
      (
        screen.getByRole("link", {
          name: /Projects: select existing or create new/i,
        }) as HTMLAnchorElement
      ).getAttribute("href"),
    ).toBe("/projects");
  });

  it("labels the projects page as the place to open an existing project", async () => {
    stubApi([existingProject]);
    renderApp(["/projects"]);

    expect(
      await screen.findByRole("heading", {
        name: /Open an existing project/i,
      }),
    ).toBeDefined();
    expect(await screen.findByText("Evidence synthesis review")).toBeDefined();
    expect(
      (
        (await screen.findByRole("link", {
          name: /Open project/i,
        })) as HTMLAnchorElement
      ).getAttribute("href"),
    ).toBe("/projects/project-1/dashboard/overview");
  });
});

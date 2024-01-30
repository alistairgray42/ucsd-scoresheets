import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import About from "./About";
import ConvertForm from "./ConvertForm";
import CreateForm from "./CreateForm";
import Info from "./Info";
import "./index.css";
import ErrorElement from "./ErrorElement";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Info />,
    errorElement: <ErrorElement />,
  },
  {
    path: "/create",
    element: <CreateForm />,
  },
  {
    path: "/convert",
    element: <ConvertForm />,
  },
  {
    path: "/about",
    element: <About />,
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);

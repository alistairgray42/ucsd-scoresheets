import { useRouteError } from "react-router";

function ErrorElement() {
  const error = useRouteError() as any;

  return (
    <div id="error-page">
      <p>
        <i>{error.statusText || error.message}</i>
      </p>
    </div>
  );
}

export default ErrorElement;

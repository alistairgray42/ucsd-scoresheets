import React from "react";
import Header from "./Header";

function CreateForm() {
  const formRef = React.useRef<HTMLFormElement>(null);

  const [error, setError] = React.useState<String | undefined>();
  const [success, setSuccess] = React.useState<String | undefined>();

  const onSubmit: React.FormEventHandler<HTMLButtonElement> = React.useCallback(
    (e) => {
      e.preventDefault();

      fetch("/create/submit", {
        method: "POST",
        body: formRef.current?.serialize(),
      }).then(async (response) => {
        const data = await response.json();

        if (data.error) {
          setSuccess(undefined);
          setError(`Error: ${data.error}`);
        } else if (data.success) {
          setError(undefined);
          setSuccess(
            `Scoresheet generation request successful. If you do not receive an email at ${data.success} within the next hour, please contact me.`,
          );
          formRef.current?.reset();
        }
      });
    },
    [],
  );

  return (
    <>
      <Header />
      <div id="wrapper">
        <h1>Create Scoresheets</h1>

        <p>
          This form allows you to create sets of UCSD Scoresheets.{" "}
          <b>
            You cannot create scoresheets unless I approve your email address
          </b>{" "}
          - due to Google&apos;s API limits, I don&apos;t plan to open this
          functionality to the general public.
        </p>

        {success && <div id="success">{success}</div>}
        {error && <div id="error"> {error}</div>}

        <form id="create-form">
          <div className="form-grid">
            <label className="input-prompt" htmlFor="tourney_name">
              Tournament name:
            </label>
            <input
              type="text"
              name="tourney_name"
              id="tourney_name"
              placeholder="Tournament name"
              required
            />

            <label className="input-prompt" htmlFor="email">
              Email:
            </label>
            <input
              type="email"
              name="email"
              id="email"
              placeholder="Email"
              required
            />

            <label className="input-prompt" htmlFor="bonus_tracking">
              Track bonus parts individually?
            </label>
            <input type="checkbox" name="bonus_tracking" id="bonus_tracking" />

            <label className="input-prompt" htmlFor="tossups_per_game">
              Tossups per game
            </label>
            <select name="tossups_per_game" id="tossups_per_game">
              <option value={20}>20</option>
              <option value={22}>22</option>
              <option value={24}>24</option>
            </select>

            <label className="input-prompt" htmlFor="rooms">
              List of rooms (max 35):
            </label>
            <textarea
              name="rooms"
              id="rooms"
              placeholder="Rooms (one per line)"
              required
            />
          </div>

          <div className="centering-div">
            <button onSubmit={onSubmit} type="submit" className="submit">
              Submit
            </button>
          </div>
        </form>
      </div>
    </>
  );
}

export default CreateForm;

import React from "react";
import Header from "./Header";

function ConvertForm() {
  const formRef = React.useRef<HTMLFormElement>(null);

  const [error, setError] = React.useState<String | undefined>();
  const [success, setSuccess] = React.useState<String | undefined>();

  const onSubmit: React.FormEventHandler<HTMLFormElement> = React.useCallback(
    (e) => {
      e.preventDefault();

      if (!formRef.current) return;
      const formData = new FormData(formRef.current);

      fetch("/convert/submit", {
        method: "POST",
        body: formData,
      }).then(async (response) => {
        if (!response.ok) {
          setError(`Error: ${response.status} ${response.statusText}`);
          return;
        }

        const data = await response.json();

        if (data.error) {
          setSuccess(undefined);
          setError(`Error: ${data.error}`);
        } else if (data.success) {
          setError(undefined);
          setSuccess(
            `Conversion request successful. Your SQBS file will be ready (in a second!) at <a href="https://ucsd-scoresheets.com/sqbs/${data.success}"> this link </a>.`,
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
        <h1>Convert to SQBS</h1>
        <p>
          This form allows you to convert UCSD scoresheets{" "}
          <b>generated by this site</b> into the standard SQBS file format.
        </p>
        <p>
          Note: This feature is experimental and should not be relied on. Use it
          at your own risk.{" "}
          <b>
            If you choose to use this feature, always have a person familiar
            with using SQBS on hand as a backup
          </b>
          , and be prepared to enter stats by hand (luckily, this is easy from
          the aggregate scoresheet!) I don&apos;t guarantee that I&apos;ll
          respond to requests for help using this feature.
        </p>
        Limitations:
        <ul>
          <li>
            This feature only supports standard game lengths and point values:
            i.e. twenty (or twenty-two or twenty-four) tossups scored 15/10/-5,
            and corresponding bonuses with three parts worth ten points each.
          </li>
          <li>
            Player names cannot be changed once the tournament starts, unless
            you manually change players&apos; names in each of the room
            spreadsheets where they played.
          </li>
          <li>
            If room spreadsheets are incorrectly filled out, conversion may be
            incorrect; if it is incorrect, you might or might not be notified of
            that. Once again, always have a person who can use SQBS on hand, and
            make sure to check SQBS files and web reports before posting
            publicly.
          </li>
          <li>
            By design, this page will only send SQBS stats to the accounts that
            created scoresheets, and will only convert the last-created set of
            scoresheets.
          </li>
        </ul>
        {success && <div id="success">{success}</div>}
        {error && <div id="error"> {error}</div>}
        <form ref={formRef} id="convert-form" onSubmit={onSubmit}>
          <div className="form-grid">
            <label className="input-prompt" htmlFor="email">
              Email:
            </label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="Email"
              required
            />

            <label className="input-prompt">Rounds to Convert:</label>
            <div id="rounds_min_max">
              <input
                type="number"
                id="rounds_min"
                name="rounds_min"
                placeholder="Start"
                min="1"
                max="16"
                required
              />
              <input
                type="number"
                id="rounds_max"
                name="rounds_max"
                placeholder="End"
                min="1"
                max="16"
                required
              />
            </div>
          </div>

          <div className="centering-div">
            <button type="submit" className="submit">
              Submit
            </button>
          </div>
        </form>
      </div>
    </>
  );
}

export default ConvertForm;

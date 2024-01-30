import Header from "./Header";

function Info() {
  return (
    <>
      <Header />
      <div id="wrapper">
        <p>
          UCSD Scoresheets are a quizbowl scorekeeping system based on Google
          Sheets. This site can be used to{" "}
          <a href="/create">create UCSD Scoresheets</a> and
          <a href="/convert"> convert them to the SQBS file format</a>.
        </p>
      </div>
    </>
  );
}

export default Info;

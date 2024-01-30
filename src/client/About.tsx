import Header from "./Header";

function About() {
  return (
    <>
      <Header />
      <div id="wrapper">
        <h1>About</h1>

        <p>
          If you&apos;re not familiar with what quizbowl is, welcome!{" "}
          <a href="https://www.qbwiki.com/wiki/Quizbowl">
            This might be a good place to start
          </a>
          .
        </p>
        <p>
          Instructions for using scoresheets created by this site can be found{" "}
          <a href="https://socalquizbowl.org/guide-to-digital-scoresheets/">
            on the Southern California Quizbowl website
          </a>
          .
        </p>
        <p>
          This site was created and is maintained by Alistair Gray, to whom you
          should direct all requests for access, questions, etc. The scoresheets
          were{" "}
          <a href="https://hsquizbowl.org/forums/viewtopic.php?f=123&t=16646">
            created by Dana Lansigan
          </a>{" "}
          and revised by Jonathan Luck, who also wrote much of the backend code.
          Versions of them have been used at most Southern California
          tournaments for years.
        </p>
      </div>
    </>
  );
}

export default About;

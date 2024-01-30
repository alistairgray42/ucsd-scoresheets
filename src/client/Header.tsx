import { Link } from "react-router-dom";

export default function Header() {
  return (
    <div id="page-header">
      <div className="header-row" id="title">
        UCSD Scoresheets
      </div>
      <div className="header-row">
        <div className="header-item">
          <Link to="/">Home</Link>
        </div>
        <div className="header-item">
          <Link to="/create">Create</Link>
        </div>
        <div className="header-item">
          <Link to="/convert">Export</Link>
        </div>
        <div className="header-item">
          <Link to="/about">About</Link>
        </div>
      </div>
    </div>
  );
}

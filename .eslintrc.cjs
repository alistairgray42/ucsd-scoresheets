module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["airbnb", "airbnb-typescript", "prettier"],
  overrides: [],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    project: "./tsconfig.json",
  },
  plugins: ["react", "prettier"],
  rules: {
    "prettier/prettier": "error",
    // not valid since react version > 17
    "react/react-in-jsx-scope": "off",
    "react/jsx-uses-react": "off",
    "jsx-a11y/label-has-associated-control": "off",
  },
};

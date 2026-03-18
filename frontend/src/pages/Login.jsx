import { useState } from "react";
import API from "../api/api";

function Login() {

  const [form, setForm] = useState({
    username: "",
    password: ""
  });

  const handleChange = (e) => {

    setForm({
      ...form,
      [e.target.name]: e.target.value
    });

  };

  const handleLogin = async () => {

    try {

      const res = await API.post("/login/all/", form);

      localStorage.setItem("access", res.data.access);
      localStorage.setItem("refresh", res.data.refresh);

      alert("Login successful");

    } catch (err) {

      console.log(err.response.data);

    }

  };

  return (

    <div>

      <h2>Login</h2>

      <input name="username" placeholder="Username or Email" onChange={handleChange} />
      <input name="password" type="password" placeholder="Password" onChange={handleChange} />

      <button onClick={handleLogin}>Login</button>

    </div>

  );
}

export default Login;
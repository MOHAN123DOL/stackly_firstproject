import { useState } from "react";
import API from "../api/api";

function Register() {

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: ""
  });

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async () => {

    try {

      const res = await API.post("jobseeker/register/", form);

      alert("Registration successful");

    } catch (err) {

      console.log(err.response.data);

    }

  };

  return (

    <div>

      <h2>Register</h2>

      <input name="username" placeholder="Username" onChange={handleChange} />
      <input name="email" placeholder="Email" onChange={handleChange} />
      <input name="password" type="password" placeholder="Password" onChange={handleChange} />
      <input name="confirm_password" type="password" placeholder="Confirm Password" onChange={handleChange} />
      <input name="phone" placeholder="Phone" onChange={handleChange} />

      <button onClick={handleSubmit}>Register</button>

    </div>

  );
}

export default Register;
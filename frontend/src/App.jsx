import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

function App() {

  return (

    <BrowserRouter>

      <Routes>

        <Route path="/login" element={<Login />} />
        <Route path="jobseeker/register" element={<Register />} />

      </Routes>

    </BrowserRouter>

  );

}

export default App;
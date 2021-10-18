

function validate()
{
    var email = document.getElementById("mail");
    var password = document.getElementById("pass");
    if(email.value.trim() == "" || password.value.trim() == "");
    {
        alert("No blank values allowed");
        return false;
    }
    else
    {
        return true;
    }
}
const buttons = document.querySelectorAll(".select-button") //returns all camera buttons a user can select

buttons.forEach(element => { //the element is the individual button within the array 'buttons'
    element.addEventListener("click", ()=> {
        //collect the data attribute on the camera for its ID, as well as the camera number
        selected_MXID = element.dataset.mxid
        num_cam = element.innerHTML
        //select the img tag holding the camera feed
        img = document.querySelector(".main-feed")
        img.src = ""
        img.src = `/video/CAM-${selected_MXID}`
        //change title above camera to reflect which cam a user is watching
        heading = document.querySelector(".cam-heading")
        heading.innerHTML = `Live Feed - ${num_cam}`
    })
});
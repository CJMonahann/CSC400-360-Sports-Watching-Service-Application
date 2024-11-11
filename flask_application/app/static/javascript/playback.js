const buttons = document.querySelectorAll(".select-button") //returns all camera buttons a user can select

buttons.forEach(element => { //the element is the individual button within the array 'buttons'
    element.addEventListener("click", ()=> {
        //collect the data attribute on the camera for its ID, as well as the camera number
        selected_MXID = element.dataset.mxid
        num_cam = element.innerHTML
        //select the img tag holding the camera feed
        img = document.querySelector(".main-feed")
        rec_link = document.querySelector(".rec-link")
        href = rec_link.href
        console.log(href)
        event_num = href.split('/')
        event_num = href.at(-1)
        img.src = ""
        img.src = `/recording/CAM-${selected_MXID}&${event_num}`
        console.log(img.src)
        //change title above camera to reflect which cam a user is watching
        heading = document.querySelector(".cam-heading")
        heading.innerHTML = `Past Feed - ${num_cam}`
    })
});
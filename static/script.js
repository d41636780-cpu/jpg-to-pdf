/* =========================================================
   JPG TO PDF CONVERTER
   FINAL SCRIPT
   ========================================================= */


/* =========================================================
   ELEMENTS
   ========================================================= */

const imageInput =
    document.getElementById("imageInput");

const dropZone =
    document.getElementById("dropZone");

const previewSection =
    document.getElementById("previewSection");

const previewContainer =
    document.getElementById("previewContainer");

const imageCount =
    document.getElementById("imageCount");

const convertForm =
    document.getElementById("convertForm");

const convertButton =
    document.getElementById("convertButton");

const buttonText =
    document.getElementById("buttonText");

const loadingText =
    document.getElementById("loadingText");

const loadingOverlay =
    document.getElementById("loadingOverlay");

const progressBar =
    document.getElementById("progressBar");

const progressPercent =
    document.getElementById("progressPercent");

const progressMessage =
    document.getElementById("progressMessage");

const progressStatus =
    document.getElementById("progressStatus");

const downloadSection =
    document.getElementById("downloadSection");

const downloadButton =
    document.getElementById("downloadButton");

const clearButton =
    document.getElementById("clearButton");

const errorMessage =
    document.getElementById("errorMessage");

const rotationData =
    document.getElementById("rotationData");


/* =========================================================
   FILE STORAGE
   ========================================================= */

let selectedFiles = [];


/* =========================================================
   SHOW ERROR
   ========================================================= */

function showError(message) {

    if (!errorMessage) {
        alert(message);
        return;
    }

    errorMessage.textContent =
        "⚠ " + message;

    errorMessage.style.display =
        "block";

}


/* =========================================================
   HIDE ERROR
   ========================================================= */

function hideError() {

    if (!errorMessage) {
        return;
    }

    errorMessage.textContent =
        "";

    errorMessage.style.display =
        "none";

}


/* =========================================================
   UPDATE IMAGE COUNT
   ========================================================= */

function updateImageCount() {

    if (!imageCount) {
        return;
    }

    const count =
        selectedFiles.length;

    imageCount.textContent =
        count +
        (count === 1 ? " image" : " images");

}


/* =========================================================
   UPDATE FILE INPUT
   ========================================================= */

function updateFileInput() {

    if (!imageInput) {
        return;
    }

    const dataTransfer =
        new DataTransfer();

    selectedFiles.forEach(
        function (file) {

            dataTransfer.items.add(file);

        }
    );

    imageInput.files =
        dataTransfer.files;

}


/* =========================================================
   UPDATE ROTATIONS
   ========================================================= */

function updateRotationData() {

    if (!rotationData) {
        return;
    }

    const rotations =
        selectedFiles.map(
            function (item) {

                return item.rotation || 0;

            }
        );

    rotationData.value =
        JSON.stringify(rotations);

}


/* =========================================================
   ADD FILES
   ========================================================= */

function addFiles(files) {

    hideError();

    const incomingFiles =
        Array.from(files);


    for (
        let i = 0;
        i < incomingFiles.length;
        i++
    ) {

        const file =
            incomingFiles[i];


        const validTypes = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ];


        if (
            !validTypes.includes(
                file.type
            )
        ) {

            showError(
                file.name +
                " is not a supported image."
            );

            continue;

        }


        if (
            file.size >
            10 * 1024 * 1024
        ) {

            showError(
                file.name +
                " is too large. Maximum size is 10 MB."
            );

            continue;

        }


        if (
            selectedFiles.length >= 20
        ) {

            showError(
                "Maximum 20 images are allowed."
            );

            break;

        }


        const alreadyExists =
            selectedFiles.some(
                function (existingFile) {

                    return (
                        existingFile.name ===
                        file.name
                        &&
                        existingFile.size ===
                        file.size
                    );

                }
            );


        if (alreadyExists) {
            continue;
        }


        file.rotation = 0;

        selectedFiles.push(file);

    }


    updateFileInput();

    updateRotationData();

    renderPreviews();

}


/* =========================================================
   REMOVE FILE
   ========================================================= */

function removeFile(index) {

    if (
        index < 0 ||
        index >= selectedFiles.length
    ) {
        return;
    }


    selectedFiles.splice(
        index,
        1
    );


    updateFileInput();

    updateRotationData();

    renderPreviews();

}


/* =========================================================
   ROTATE FILE
   ========================================================= */

function rotateFile(index) {

    if (
        !selectedFiles[index]
    ) {
        return;
    }


    let currentRotation =
        selectedFiles[index].rotation || 0;


    currentRotation += 90;


    if (
        currentRotation >= 360
    ) {

        currentRotation = 0;

    }


    selectedFiles[index].rotation =
        currentRotation;


    updateRotationData();

    renderPreviews();

}


/* =========================================================
   RENDER PREVIEWS
   ========================================================= */

function renderPreviews() {

    if (!previewContainer) {
        return;
    }


    previewContainer.innerHTML =
        "";


    updateImageCount();


    if (
        selectedFiles.length === 0
    ) {

        if (previewSection) {

            previewSection.style.display =
                "none";

        }

        return;

    }


    if (previewSection) {

        previewSection.style.display =
            "block";

    }


    selectedFiles.forEach(
        function (file, index) {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "preview-card";


            card.draggable =
                true;


            card.dataset.index =
                index;


            const image =
                document.createElement(
                    "img"
                );


            image.className =
                "preview-image";


            image.alt =
                file.name;


            image.style.transform =
                "rotate(" +
                (file.rotation || 0) +
                "deg)";


            const objectUrl =
                URL.createObjectURL(
                    file
                );


            image.src =
                objectUrl;


            image.onload =
                function () {

                    URL.revokeObjectURL(
                        objectUrl
                    );

                };


            const info =
                document.createElement(
                    "div"
                );


            info.className =
                "preview-info";


            const name =
                document.createElement(
                    "div"
                );


            name.className =
                "preview-name";


            name.textContent =
                file.name;


            const number =
                document.createElement(
                    "div"
                );


            number.className =
                "preview-number";


            number.textContent =
                "Page " +
                (index + 1);


            info.appendChild(
                number
            );

            info.appendChild(
                name
            );


            const controls =
                document.createElement(
                    "div"
                );


            controls.className =
                "preview-controls";


            const rotateButton =
                document.createElement(
                    "button"
                );


            rotateButton.type =
                "button";


            rotateButton.className =
                "thumbnail-button";


            rotateButton.textContent =
                "↻ Rotate";


            rotateButton.addEventListener(
                "click",
                function () {

                    rotateFile(index);

                }
            );


            const removeButton =
                document.createElement(
                    "button"
                );


            removeButton.type =
                "button";


            removeButton.className =
                "thumbnail-button remove-button";


            removeButton.textContent =
                "✕ Remove";


            removeButton.addEventListener(
                "click",
                function () {

                    removeFile(index);

                }
            );


            controls.appendChild(
                rotateButton
            );


            controls.appendChild(
                removeButton
            );


            card.appendChild(
                image
            );


            card.appendChild(
                info
            );


            card.appendChild(
                controls
            );


            previewContainer.appendChild(
                card
            );

        }
    );


    enableDragAndDrop();

}


/* =========================================================
   DRAG & DROP REORDER
   ========================================================= */

function enableDragAndDrop() {

    const cards =
        previewContainer.querySelectorAll(
            ".preview-card"
        );


    let draggedIndex =
        null;


    cards.forEach(
        function (card) {

            card.addEventListener(
                "dragstart",
                function () {

                    draggedIndex =
                        Number(
                            card.dataset.index
                        );

                    card.classList.add(
                        "dragging"
                    );

                }
            );


            card.addEventListener(
                "dragend",
                function () {

                    card.classList.remove(
                        "dragging"
                    );

                }
            );


            card.addEventListener(
                "dragover",
                function (event) {

                    event.preventDefault();

                }
            );


            card.addEventListener(
                "drop",
                function (event) {

                    event.preventDefault();


                    const targetIndex =
                        Number(
                            card.dataset.index
                        );


                    if (
                        draggedIndex === null ||
                        draggedIndex ===
                        targetIndex
                    ) {
                        return;
                    }


                    const movedFile =
                        selectedFiles[
                            draggedIndex
                        ];


                    selectedFiles.splice(
                        draggedIndex,
                        1
                    );


                    selectedFiles.splice(
                        targetIndex,
                        0,
                        movedFile
                    );


                    draggedIndex =
                        null;


                    updateFileInput();

                    updateRotationData();

                    renderPreviews();

                }
            );

        }
    );

}


/* =========================================================
   FILE INPUT
   ========================================================= */

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            addFiles(
                imageInput.files
            );

        }
    );

}


/* =========================================================
   DRAG & DROP UPLOAD
   ========================================================= */

if (dropZone) {

    dropZone.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            dropZone.classList.add(
                "drag-over"
            );

        }
    );


    dropZone.addEventListener(
        "dragleave",
        function () {

            dropZone.classList.remove(
                "drag-over"
            );

        }
    );


    dropZone.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();


            dropZone.classList.remove(
                "drag-over"
            );


            addFiles(
                event.dataTransfer.files
            );

        }
    );

}


/* =========================================================
   CLEAR ALL
   ========================================================= */

if (clearButton) {

    clearButton.addEventListener(
        "click",
        function () {

            selectedFiles = [];


            if (imageInput) {

                imageInput.value =
                    "";

            }


            updateFileInput();

            updateRotationData();

            renderPreviews();

            hideError();


            if (downloadSection) {

                downloadSection.style.display =
                    "none";

            }

        }
    );

}


/* =========================================================
   PROGRESS
   ========================================================= */

function setProgress(
    percent,
    message,
    status
) {

    if (progressBar) {

        progressBar.style.width =
            percent + "%";

    }


    if (progressPercent) {

        progressPercent.textContent =
            percent + "%";

    }


    if (progressMessage) {

        progressMessage.textContent =
            message;

    }


    if (progressStatus) {

        progressStatus.textContent =
            status;

    }

}


/* =========================================================
   RESET CONVERT BUTTON
   ========================================================= */

function resetConvertButton() {

    if (convertButton) {

        convertButton.disabled =
            false;

    }


    if (buttonText) {

        buttonText.style.display =
            "inline";

    }


    if (loadingText) {

        loadingText.style.display =
            "none";

    }

}


/* =========================================================
   CONVERT FORM
   ========================================================= */

if (convertForm) {

    convertForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            hideError();


            if (
                selectedFiles.length === 0
            ) {

                showError(
                    "Please select at least one image."
                );

                return;

            }


            if (
                selectedFiles.length > 20
            ) {

                showError(
                    "Maximum 20 images are allowed."
                );

                return;

            }


            updateFileInput();

            updateRotationData();


            if (downloadSection) {

                downloadSection.style.display =
                    "none";

            }


            if (loadingOverlay) {

                loadingOverlay.style.display =
                    "flex";

            }


            if (convertButton) {

                convertButton.disabled =
                    true;

            }


            if (buttonText) {

                buttonText.style.display =
                    "none";

            }


            if (loadingText) {

                loadingText.style.display =
                    "inline";

            }


            setProgress(
                10,
                "Preparing your images...",
                "Starting conversion..."
            );


            const progressSteps = [

                {
                    percent: 25,
                    message: "Reading images...",
                    status: "Processing files..."
                },

                {
                    percent: 45,
                    message: "Optimizing images...",
                    status: "Preparing PDF pages..."
                },

                {
                    percent: 65,
                    message: "Creating PDF pages...",
                    status: "Building your PDF..."
                },

                {
                    percent: 80,
                    message: "Finalizing PDF...",
                    status: "Almost finished..."
                },

                {
                    percent: 90,
                    message: "Saving your PDF...",
                    status: "Finishing..."
                }

            ];


            let progressIndex =
                0;


            const progressTimer =
                setInterval(
                    function () {

                        if (
                            progressIndex <
                            progressSteps.length
                        ) {

                            const step =
                                progressSteps[
                                    progressIndex
                                ];


                            setProgress(
                                step.percent,
                                step.message,
                                step.status
                            );


                            progressIndex++;

                        }

                    },
                    600
                );


            try {

                const formData =
                    new FormData(
                        convertForm
                    );


                const response =
                    await fetch(
                        "/convert",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                clearInterval(
                    progressTimer
                );


                const responseText =
                    await response.text();


                if (!response.ok) {

                    throw new Error(
                        responseText ||
                        "PDF creation failed."
                    );

                }


                let result;


                try {

                    result =
                        JSON.parse(
                            responseText
                        );

                } catch (jsonError) {

                    throw new Error(
                        "Server returned an invalid response."
                    );

                }


                if (
                    !result.success
                ) {

                    throw new Error(
                        "PDF creation failed."
                    );

                }


                setProgress(
                    100,
                    "PDF created successfully!",
                    "Your PDF is ready."
                );


                setTimeout(
                    function () {

                        if (loadingOverlay) {

                            loadingOverlay.style.display =
                                "none";

                        }


                        resetConvertButton();


                        if (downloadButton) {

                            downloadButton.href =
                                result.download_url;

                        }


                        if (downloadSection) {

                            downloadSection.style.display =
                                "block";

                        }

                    },
                    500
                );


            } catch (error) {

                clearInterval(
                    progressTimer
                );


                console.error(
                    "Conversion error:",
                    error
                );


                if (loadingOverlay) {

                    loadingOverlay.style.display =
                        "none";

                }


                resetConvertButton();


                let message =
                    error.message;


                if (!message) {

                    message =
                        "Something went wrong while creating the PDF.";

                }


                showError(
                    message
                );

            }

        }
    );

}


/* =========================================================
   INITIAL STATE
   ========================================================= */

updateImageCount();

updateRotationData();

hideError();


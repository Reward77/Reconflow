protectPage();

let jobs = [];
let uploads = [];

let companyColumns = [];
let processorColumns = [];

let selectedJobId = null;
let selectedCompanyFile = null;
let selectedProcessorFile = null;


document.addEventListener("DOMContentLoaded", async () => {

    await loadJobs();

    document
        .getElementById("jobSelect")
        .addEventListener(
            "change",
            handleJobChange
        );

    document
        .getElementById("detectColumnsBtn")
        .addEventListener(
            "click",
            detectColumns
        );

    document
        .getElementById("saveMappingBtn")
        .addEventListener(
            "click",
            saveMapping
        );

    document
        .getElementById("resetMappingBtn")
        .addEventListener(
            "click",
            resetMapping
        );

});


/* =========================================
   LOAD JOBS
========================================= */

async function loadJobs() {

    try {

        const response = await api("/jobs");

        if (Array.isArray(response)) {
            jobs = response;
        }
        else if (Array.isArray(response?.jobs)) {
            jobs = response.jobs;
        }
        else {
            jobs = [];
        }

        const select =
            document.getElementById("jobSelect");

        select.innerHTML = `
            <option value="">
                Select a reconciliation job
            </option>
        `;

        jobs.forEach(job => {

            const option =
                document.createElement("option");

            option.value = job.id;

            option.textContent =
                job.job_name ||
                job.name ||
                "Unnamed Job";

            select.appendChild(option);

        });

    }
    catch (error) {

        console.error(
            "Failed to load jobs:",
            error
        );

        alert(
            error.message ||
            "Unable to load jobs."
        );

    }

}


/* =========================================
   JOB CHANGE
========================================= */

async function handleJobChange(event) {

    selectedJobId =
        event.target.value;

    resetMapping();

    if (!selectedJobId) {

        document.getElementById(
            "fileSection"
        ).style.display = "none";

        return;
    }

    document.getElementById(
        "fileSection"
    ).style.display = "block";


    await loadUploadsForJob(
        selectedJobId
    );

}


/* =========================================
   LOAD UPLOADS
========================================= */

async function loadUploadsForJob(jobId) {

    try {

        const response =
            await api(`/uploads/job/${jobId}`);


        if (Array.isArray(response)) {
            uploads = response;
        }
        else if (Array.isArray(response?.uploads)) {
            uploads = response.uploads;
        }
        else {
            uploads = [];
        }


        const jobUploads =
            uploads.filter(upload => {

                const uploadJobId =
                    upload.job_id ||
                    upload.job?.id;

                return String(uploadJobId)
                    === String(jobId);

            });


        populateFileSelects(
            jobUploads
        );

        updateSelectedFilePreview();

    }
    catch (error) {

        console.error(
            "Failed to load uploads:",
            error
        );

        alert(
            error.message ||
            "Unable to load uploads."
        );

    }

}


/* =========================================
   POPULATE FILES
========================================= */

function populateFileSelects(jobUploads) {

    const companySelect =
        document.getElementById(
            "companyFile"
        );

    const processorSelect =
        document.getElementById(
            "processorFile"
        );


    companySelect.innerHTML = `
        <option value="">
            Select company file
        </option>
    `;

    processorSelect.innerHTML = `
        <option value="">
            Select processor file
        </option>
    `;


    jobUploads.forEach(upload => {

        const type =
            String(
                upload.file_type ||
                upload.upload_type ||
                upload.type ||
                ""
            ).toLowerCase();


        const fileName =
            upload.original_filename ||
            upload.filename ||
            upload.file_name ||
            "Unnamed file";


        const option =
            document.createElement("option");

        option.value =
            upload.id;

        option.textContent =
            fileName;


        if (type === "company") {

            companySelect.appendChild(
                option
            );

        }
        else if (type === "processor") {

            processorSelect.appendChild(
                option
            );

        }

    });

    companySelect.onchange = updateSelectedFilePreview;
    processorSelect.onchange = updateSelectedFilePreview;

}


function updateSelectedFilePreview() {
    const companyOption =
        document.getElementById(
            "companyFile"
        );
    const processorOption =
        document.getElementById(
            "processorFile"
        );

    const companyLabel =
        companyOption.selectedOptions[0]?.textContent ||
        "No file selected";
    const processorLabel =
        processorOption.selectedOptions[0]?.textContent ||
        "No file selected";

    document.getElementById(
        "companyFileName"
    ).innerText =
        companyOption.value
            ? companyLabel
            : "No file selected";

    document.getElementById(
        "processorFileName"
    ).innerText =
        processorOption.value
            ? processorLabel
            : "No file selected";
}


async function detectColumns() {
    selectedCompanyFile =
        document.getElementById(
            "companyFile"
        ).value;

    selectedProcessorFile =
        document.getElementById(
            "processorFile"
        ).value;

    if (!selectedCompanyFile) {
        alert(
            "Please select a company file."
        );
        return;
    }

    if (!selectedProcessorFile) {
        alert(
            "Please select a processor file."
        );
        return;
    }

    const button =
        document.getElementById(
            "detectColumnsBtn"
        );

    button.disabled = true;
    button.innerText =
        "Detecting columns...";

    try {
        const response =
            await api(
                `/uploads/${selectedCompanyFile}/columns`
            );

        companyColumns =
            response.company_columns ||
            response.columns ||
            [];

        const processorResponse =
            await api(
                `/uploads/${selectedProcessorFile}/columns`
            );

        processorColumns =
            processorResponse.processor_columns ||
            processorResponse.columns ||
            [];

        populateColumnSelects();

        document.getElementById(
            "mappingSection"
        ).style.display = "block";

        document.getElementById(
            "mappingSection"
        ).scrollIntoView({
            behavior: "smooth"
        });
    }
    catch (error) {
        console.error(
            "Column detection failed:",
            error
        );

        alert(
            error.message ||
            "Unable to detect file columns."
        );
    }
    finally {
        button.disabled = false;
        button.innerText =
            "Detect Columns";
    }
}


/* =========================================
   POPULATE COLUMN DROPDOWNS
========================================= */

function populateColumnSelects() {

    const companyFields = [
        "company_transaction_id",
        "company_amount",
        "company_status",
        "company_date",
        "company_reference"
    ];

    const processorFields = [
        "processor_transaction_id",
        "processor_amount",
        "processor_status",
        "processor_date",
        "processor_reference"
    ];


    companyFields.forEach(id => {

        populateSelect(
            document.getElementById(id),
            companyColumns
        );

    });


    processorFields.forEach(id => {

        populateSelect(
            document.getElementById(id),
            processorColumns
        );

    });

}


/* =========================================
   SELECT HELPER
========================================= */

function populateSelect(
    select,
    columns
) {

    select.innerHTML = `
        <option value="">
            Select column
        </option>
    `;


    columns.forEach(column => {

        const option =
            document.createElement("option");

        option.value = column;

        option.textContent = column;

        select.appendChild(option);

    });

}


/* =========================================
   SAVE MAPPING
========================================= */

async function saveMapping() {

    const mapping = {

        job_id: selectedJobId,

        company_file_id:
            selectedCompanyFile,

        processor_file_id:
            selectedProcessorFile,

        company: {

            transaction_id:
                getValue(
                    "company_transaction_id"
                ),

            amount:
                getValue(
                    "company_amount"
                ),

            status:
                getValue(
                    "company_status"
                ),

            date:
                getValue(
                    "company_date"
                ),

            reference:
                getValue(
                    "company_reference"
                )

        },

        processor: {

            transaction_id:
                getValue(
                    "processor_transaction_id"
                ),

            amount:
                getValue(
                    "processor_amount"
                ),

            status:
                getValue(
                    "processor_status"
                ),

            date:
                getValue(
                    "processor_date"
                ),

            reference:
                getValue(
                    "processor_reference"
                )

        }

    };


    if (
        !mapping.company.transaction_id ||
        !mapping.processor.transaction_id
    ) {

        alert(
            "Transaction ID must be mapped on both files."
        );

        return;

    }


    if (
        !mapping.company.amount ||
        !mapping.processor.amount
    ) {

        alert(
            "Amount must be mapped on both files."
        );

        return;

    }


    const button =
        document.getElementById(
            "saveMappingBtn"
        );

    button.disabled = true;

    button.innerText =
        "Saving...";


    try {

        /*
         * Backend endpoint expected:
         *
         * POST /mapping
         */

        const response =
            await api(
                "/mapping",
                "POST",
                mapping
            );


        console.log(
            "Mapping saved:",
            response
        );


        document.getElementById(
            "mappingStatus"
        ).innerText =
            "Saved";


        document.getElementById(
            "mappingStatus"
        ).style.background =
            "#dcfce7";


        document.getElementById(
            "mappingStatus"
        ).style.color =
            "#166534";


        document.getElementById(
            "mappingSummary"
        ).style.display =
            "flex";


    }
    catch (error) {

        console.error(
            "Failed to save mapping:",
            error
        );

        alert(
            error.message ||
            "Unable to save mapping."
        );

    }
    finally {

        button.disabled = false;

        button.innerText =
            "Save Mapping";

    }

}


/* =========================================
   RESET
========================================= */

function resetMapping() {

    document.getElementById(
        "mappingSection"
    ).style.display = "none";


    document.getElementById(
        "mappingSummary"
    ).style.display = "none";


    document.getElementById(
        "mappingStatus"
    ).innerText =
        "Not saved";


    companyColumns = [];

    processorColumns = [];

}


/* =========================================
   HELPER
========================================= */

function getValue(id) {

    return document
        .getElementById(id)
        .value;

}

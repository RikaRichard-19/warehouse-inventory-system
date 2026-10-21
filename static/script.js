let currentBarcode = "";


// ===============================
// SEARCH ITEM
// ===============================

async function searchItem() {

    currentBarcode =
        document.getElementById("barcode").value.trim();

    if (currentBarcode === "") {

        alert("Please enter a barcode");

        return;
    }

    const response = await fetch("/search", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            barcode: currentBarcode
        })
    });

    const data = await response.json();

    if (data.success) {

        // Show item name
        document.getElementById("itemName").innerText =
            data.name;

        // Show quantity
        document.getElementById("quantity").innerText =
            data.quantity;

        // Show location
        document.getElementById("location").innerText =
            data.location;

        // Show current stock in card
        document.getElementById("currentStock").innerText =
            data.quantity;

        // Reset added/removed values
        document.getElementById("stockAdded").innerText =
            "0";

        document.getElementById("stockRemoved").innerText =
            "0";

        // Show message
        document.getElementById("message").innerText =
            "✅ Item found successfully";

    } else {

        alert(data.message);
    }
}


// ===============================
// UPDATE STOCK
// ===============================

async function updateStock(operation) {

    const quantity =
        parseInt(
            document.getElementById("updateQuantity").value
        );


    // Check quantity
    if (!quantity || quantity <= 0) {

        alert("Enter a valid quantity");

        return;
    }


    // Check whether item was searched
    if (currentBarcode === "") {

        alert("Please search for an item first");

        return;
    }


    // Send request to Flask
    const response = await fetch("/update", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            barcode: currentBarcode,

            operation: operation,

            quantity: quantity
        })
    });


    const data = await response.json();


    // ===============================
    // SUCCESS
    // ===============================

    if (data.success) {

        // Update quantity in Item Details
        document.getElementById("quantity").innerText =
            data.quantity;


        // Update Current Stock card
        document.getElementById("currentStock").innerText =
            data.quantity;


        // ===============================
        // STOCK ADDED
        // ===============================

        if (operation === "ADD") {

            // Show added quantity
            document.getElementById("stockAdded").innerText =
                quantity;

            // Show success message
            document.getElementById("message").innerText =
                "✅ Stock Added Successfully! " +
                quantity +
                " units added. Current Stock: " +
                data.quantity;
        }


        // ===============================
        // STOCK REMOVED
        // ===============================

        else if (operation === "REMOVE") {

            // Show removed quantity
            document.getElementById("stockRemoved").innerText =
                quantity;

            // Show success message
            document.getElementById("message").innerText =
                "✅ Stock Removed Successfully! " +
                quantity +
                " units removed. Current Stock: " +
                data.quantity;
        }


        // Clear quantity input
        document.getElementById("updateQuantity").value = "";

    }


    // ===============================
    // ERROR
    // ===============================

    else {

        document.getElementById("message").innerText =
            "❌ " + data.message;
    }
}
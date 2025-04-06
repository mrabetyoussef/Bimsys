document.addEventListener('DOMContentLoaded', function() {
    // Find all table rows that have a data-href attribute
    document.querySelectorAll('tr[data-href]').forEach(function(row) {
      row.addEventListener('click', function() {
        // Get the value of the data-href attribute from the clicked row
        const targetUrl = row.getAttribute('data-href');
        console.log('Row clicked, target URL:', targetUrl);
        // Redirect to the target URL
        window.location.href = targetUrl;
      });
    });
  });
  
# graf-report
     v1.1 - Added Static Panel Renderer URL Path segment as a parameter (-Z)
            In the latest version of Grafana renderer a unique element is added to the URL for each dashboard
            and this must be inserted into the renderer request URL
Python App to generate simple e-mail reports from Grafana dashboards.

Enables dashboards to be sent as e-mail with embedded images.

Creates an email with embedded images for each panel on the dashboard.

    # Daily Level Report parameter example
    # min stat - ('water-24h-view',6,400,100)
    # max stat - ('water-24h-view',8,400,100)
    # graph    - ('water-24h-view',2,800,400)
    # alerts   - ('water-24h-view',4,800,150)

    # HTML Template Example
    # |------------------|
    # |   Min   |  Max   |
    # |------------------|
    # |    Main Graph    |
    # |------------------|
    # |      Alerts      |
    # |------------------|

    #<html>
    #    <body>
    #       <p>Daily Tank Level Report for last 24 hours.<br>
    #       <table>
    #           <tr>
    #               <td> <img src="cid:img_water-24h-view-6.png" alt="Minimum Tank Level"> </td>
    #               <td> <img src="cid:img_water-24h-view-8.png" alt="Maximum Tank Level"> </td>
    #           </tr>
    #           <tr>
    #               <td  colspan="2"> <img src="cid:img_water-24h-view-2.png" alt="Tank Level Chart"> </td>
    #           </tr>
    #           <tr>
    #               <td  colspan="2"> <img src="cid:img_water-24h-view-4.png" alt="Alerts"> </td>
    #           </tr>
    #       </table>
    #    </body>
    #</html>

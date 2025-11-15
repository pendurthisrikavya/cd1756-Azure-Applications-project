# Writeup – Deployment Choice and Justification

## 1. App Service vs Virtual Machine

### A. Virtual Machine (VM)

**Cost:**  
A VM usually costs more because it runs all the time, even when the app is not being used. You also need extra storage and networking, which adds to the price.

**Scalability:**  
Scaling a VM requires doing things manually, like upgrading the VM size or setting up load balancers. This takes more time and effort.

**Availability:**  
You are responsible for keeping the VM updated, installing patches, restarting services, and making sure the app stays online. This increases the chances of downtime.

**Workflow:**  
You must install and manage everything yourself (Python, packages, web server, OS updates, security). This makes the overall workflow more complicated.

---

### B. App Service

**Cost:**  
App Service is generally cheaper and more efficient for web apps because you only pay for the App Service Plan. Azure automatically handles the underlying servers.

**Scalability:**  
Scaling is very easy. You can scale up or out with just a click. Azure automatically manages load balancing for you.

**Availability:**  
Azure takes care of OS updates, patches, and server maintenance. This means the app is more reliable and requires less work from the developer.

**Workflow:**  
App Service makes deployment very simple (GitHub Actions, zip deploy, or local deploy). It integrates smoothly with Storage and SQL Database without extra setup.

---

## ✔ My Choice

I chose **Azure App Service** because it is easier to manage, cheaper for this type of project, and provides automatic scaling and updates. Since the CMS app is a simple Flask application, App Service fits perfectly and avoids all the heavy work required with a VM. It also integrates nicely with Azure SQL, Storage, and Microsoft Authentication.

---

## 2. What could make me choose a VM instead?

I would choose a VM if the application needed more control over the operating system, required installing custom software, or needed background services that App Service cannot support.  
A VM also makes sense if the app needs special network configurations or very high performance that requires full control over CPU, memory, or GPU.  
If the CMS app became much larger or required custom system-level features, then switching to a VM would make more sense.


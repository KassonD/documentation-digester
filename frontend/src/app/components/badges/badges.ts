import { Component, input } from '@angular/core';

@Component({
  selector: 'app-badges',
  imports: [],
  templateUrl: './badges.html',
  styleUrl: './badges.css',
})

export class Badges {
  fileName = input<string>("N/A");
}

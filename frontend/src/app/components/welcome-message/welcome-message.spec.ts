import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WelcomeMessage } from './welcome-message';

describe('WelcomeMessage', () => {
  let component: WelcomeMessage;
  let fixture: ComponentFixture<WelcomeMessage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WelcomeMessage]
    })
      .compileComponents();

    fixture = TestBed.createComponent(WelcomeMessage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
